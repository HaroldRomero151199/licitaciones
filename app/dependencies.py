from app.application.ingestion_service import IngestionService
from app.application.active_ingestion_service import TenderIngestionService
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
