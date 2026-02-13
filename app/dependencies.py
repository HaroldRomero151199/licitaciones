from functools import lru_cache
import secrets
from typing import Optional

from fastapi import Header, HTTPException, Depends

from app.application.ingestion_service import IngestionService
from app.application.active_ingestion_service import TenderIngestionService
from app.application.daily_ingestion_runner import DailyIngestionRunner
from app.infrastructure.mercadopublico.client import MercadoPublicoClient
from app.infrastructure.solr.repository import SolrTenderRepository
from app.config import settings

def get_mercado_publico_client():
    return MercadoPublicoClient(
        ticket=settings.mp_ticket,
        base_url=settings.mp_base_url
    )

def get_solr_repository():
    return SolrTenderRepository(
        base_url=settings.solr_base_url,
        core=settings.solr_core,
        username=settings.solr_username,
        password=settings.solr_password
    )

def get_ingestion_service():
    # Usamos el cliente real para la ingesta
    real_client = get_mercado_publico_client()
    return IngestionService(
        mp_client=real_client,
        solr_url=settings.solr_base_url 
    )

def get_active_ingestion_service():
    real_client = get_mercado_publico_client()
    solr_repo = get_solr_repository()
    return TenderIngestionService(
        mp_client=real_client,
        solr_repo=solr_repo
    )

@lru_cache()
def get_daily_ingestion_runner() -> DailyIngestionRunner:
    """
    Singleton instance of DailyIngestionRunner.
    Ensures that the asyncio.Lock is shared across requests.
    """
    # We need to manually construct dependencies here or use a provider.
    # Since get_active_ingestion_service creates new instances every time,
    # we might want to store the service instance too if we want it to be singleton,
    # but the critical part is the Runner which holds the Lock.
    # The inner service is stateless so it's fine to recreate or modify get_active_ingestion_service to be cached too.
    # For now, let's just create a new service instance for the runner, but keep the runner singleton.
    service = get_active_ingestion_service()
    return DailyIngestionRunner(ingestion_service=service)

async def require_admin_token(x_admin_token: Optional[str] = Header(None, alias="X-ADMIN-TOKEN")):
    if x_admin_token is None:
        raise HTTPException(status_code=401, detail="Missing X-ADMIN-TOKEN header")
    
    if not secrets.compare_digest(x_admin_token, settings.admin_token):
        raise HTTPException(status_code=401, detail="Invalid admin token")
    
    return x_admin_token
