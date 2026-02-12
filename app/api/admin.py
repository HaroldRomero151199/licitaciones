from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any

from app.application.active_ingestion_service import TenderIngestionService
from app.dependencies import get_active_ingestion_service
from app.domain.schemas import LicitacionEstado

router = APIRouter(prefix="/admin", tags=["Admin"])

@router.post(
    "/ingestion/delta",
    responses={
        500: {"description": "Internal Server Error or Ingestion Error"},
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
