import asyncio
import logging
from app.infrastructure.mercadopublico.client import MercadoPublicoClient
from app.infrastructure.solr.repository import SolrTenderRepository
from app.application.active_ingestion_service import TenderIngestionService
from app.config import settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def verify_delta_sync():
    """
    Simulates the delta sync process for 'activas' to verify the implementation.
    """
    logger.info("Initializing services...")
    
    mp_client = MercadoPublicoClient(
        ticket=settings.mp_ticket,
        base_url=settings.mp_base_url
    )
    
    solr_repo = SolrTenderRepository(
        base_url=settings.solr_base_url,
        core=settings.solr_core,
        username=settings.solr_username,
        password=settings.solr_password
    )
    
    ingestion_service = TenderIngestionService(mp_client, solr_repo)
    
    logger.info("Starting Delta Sync Verification...")
    
    try:
        # Run delta sync for 'activas'
        stats = await ingestion_service.ingest_by_status_delta("activas")
        
        logger.info("Verification Completed Successfully!")
        logger.info(f"Stats: {stats}")
        
    except Exception as e:
        logger.error(f"Verification Failed: {e}")
    finally:
        await mp_client.close()

if __name__ == "__main__":
    asyncio.run(verify_delta_sync())
