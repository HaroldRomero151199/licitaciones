from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any

from app.application.active_ingestion_service import ActiveTendersIngestionService
from app.dependencies import get_active_ingestion_service

router = APIRouter(prefix="/admin", tags=["Admin"])

@router.post(
    "/ingestion/actives",
    responses={
        500: {"description": "Internal Server Error or Ingestion Error"},
        503: {"description": "Service Unavailable - Mercado Público API is overloaded"}
    }
)
async def ingest_actives(
    service: ActiveTendersIngestionService = Depends(get_active_ingestion_service)
) -> Dict[str, Any]:
    """
    Trigger ingestion of active tenders from Mercado Público to Solr.
    
    Returns:
        Dict with execution summary (found, indexed, errors, time).
    """
    result = await service.ingest_actives()
    
    if result.get("status") == "error":
        raise HTTPException(status_code=500, detail=result)
        
    return result
