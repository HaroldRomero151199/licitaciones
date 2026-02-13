from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from typing import Dict, Any

from app.application.active_ingestion_service import TenderIngestionService
from app.application.daily_ingestion_runner import DailyIngestionRunner
from app.dependencies import get_active_ingestion_service, require_admin_token, get_daily_ingestion_runner
from app.domain.schemas import LicitacionEstado

# Protect all admin endpoints with the admin token
router = APIRouter(
    prefix="/admin", 
    tags=["Admin"],
    dependencies=[Depends(require_admin_token)]
)

@router.post(
    "/ingestion/delta",
    responses={
        500: {"description": "Internal Server Error or Ingestion Error"},
        401: {"description": "Unauthorized"},
    }
)
async def ingest_delta(
    status: LicitacionEstado = LicitacionEstado.activas,
    service: TenderIngestionService = Depends(get_active_ingestion_service)
) -> Dict[str, Any]:
    """
    Trigger incremental ingestion (delta sync) by status.
    
    Args:
        status: activas, publicada, cerrada, desierta, adjudicada, revocada, suspendida.
    """
    # service is injected as TenderIngestionService instance provided by get_active_ingestion_service
    result = await service.ingest_by_status_delta(status.value)
    
    if result.get("status") == "error":
        raise HTTPException(status_code=500, detail=result)
        
    return result

@router.post(
    "/ingestion/daily",
    responses={
        200: {"description": "Daily ingestion finished successfully (or with partial errors)"},
        409: {"description": "Daily ingestion already running"},
        401: {"description": "Unauthorized"},
    }
)
async def run_daily_ingestion_now(
    runner: DailyIngestionRunner = Depends(get_daily_ingestion_runner)
) -> Dict[str, Any]:
    """
    Trigger the daily sequential ingestion process immediately.
    This runs ingestion for all statuses in order:
    activas -> publicada -> cerrada -> desierta -> adjudicada -> revocada -> suspendida
    
    If a run is already in progress, returns 409 Conflict.
    """
    try:
        return await runner.run_daily_sequence()
    except RuntimeError as e:
        if "already running" in str(e):
            raise HTTPException(status_code=409, detail="Daily ingestion already running")
        raise e
