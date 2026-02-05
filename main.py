import os
import logging
from datetime import date
from fastapi import FastAPI, Depends
from dotenv import load_dotenv

from app.application.ingestion_service import IngestionService
from app.infrastructure.external.mock_client import MockMercadoPublicoClient

# Load env variables
load_dotenv()

# Logging config
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Mercado Público Search API")

# Dependency Injection setup
def get_ingestion_service():
    # Usamos el MockClient por defecto como se solicitó
    mock_client = MockMercadoPublicoClient(
        list_file=os.getenv("MOCK_LIST_JSON", "licitaciones_list 2-3.json"),
        detail_file=os.getenv("MOCK_DETAIL_JSON", "licitacion 2732-49-LE25.json")
    )
    return IngestionService(
        mp_client=mock_client,
        solr_url=os.getenv("SOLR_URL", "")
    )

@app.get("/")
async def root():
    return {"message": "Mercado Público Search Ingestor Active"}

@app.post("/ingest/test")
async def ingest_test(service: IngestionService = Depends(get_ingestion_service)):
    # Simular ingesta para la fecha de hoy
    results = await service.ingest_by_date(date.today())
    return {
        "status": "success",
        "processed_count": len(results),
        "sample": results[0] if results else None
    }

@app.get("/search")
async def search(q: str):
    # Placeholder for Solr search
    return {"query": q, "results": [], "note": "Solr search not implemented yet"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
