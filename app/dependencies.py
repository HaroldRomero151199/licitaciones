from app.application.ingestion_service import IngestionService
from app.infrastructure.mercadopublico.client import MercadoPublicoClient
from app.config import settings

def get_mercado_publico_client():
    return MercadoPublicoClient(
        ticket=settings.mp_ticket,
        base_url=settings.mp_base_url
    )

def get_ingestion_service():
    # Usamos el cliente real para la ingesta
    real_client = get_mercado_publico_client()
    return IngestionService(
        mp_client=real_client,
        solr_url=settings.solr_url
    )
