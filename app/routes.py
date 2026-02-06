from datetime import date
from fastapi import APIRouter, Depends
from app.application.ingestion_service import IngestionService
from app.dependencies import get_ingestion_service

router = APIRouter()

@router.get("/")
async def root():
    return {"message": "Mercado Público Search Ingestor Active"}

@router.post("/ingest/test")
async def ingest_test(service: IngestionService = Depends(get_ingestion_service)):
    # Simular ingesta para la fecha de hoy
    results = await service.ingest_by_date(date.today())
    return {
        "status": "success",
        "processed_count": len(results),
        "sample": results[0] if results else None
    }

@router.get("/search")
async def search(q: str):
    # Placeholder for Solr search
    return {"query": q, "results": [], "note": "Solr search not implemented yet"}
