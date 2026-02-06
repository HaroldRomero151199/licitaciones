import logging
from datetime import date
from typing import List
from app.domain.ports import MercadoPublicoClientPort
from app.application.transformer_service import TenderTransformer

logger = logging.getLogger(__name__)

class IngestionService:
    def __init__(self, mp_client: MercadoPublicoClientPort, solr_url: str):
        self.mp_client = mp_client
        self.solr_url = solr_url

    async def ingest_by_date(self, target_date: date):
        logger.info(f"Starting ingestion for date: {target_date}")
        
        # 1. Obtener lista
        licitaciones_list = await self.mp_client.get_daily_list(target_date)
        logger.info(f"Found {len(licitaciones_list)} licitaciones in list")
        
        documents = []
        for summary in licitaciones_list:
            try:
                # 2. Obtener detalle
                detail = await self.mp_client.get_detail(summary.codigo_externo)
                
                # 3. Transformar usando el servicio unificado
                doc = TenderTransformer.to_index_doc(detail)
                documents.append(doc.model_dump(by_alias=True))
                
                logger.debug(f"Processed: {detail.codigo_externo}")
            except Exception as e:
                logger.error(f"Error processing {summary.codigo_externo}: {e}")

        # 4. Enviar a Solr
        logger.info(f"Indexable documents: {len(documents)}")
        if self.solr_url:
            logger.info(f"Sending data to Solr at {self.solr_url}...")
            # Aquí irá la lógica de pysolr
        else:
            logger.warning("No Solr URL provided, skipping indexing.")
            
        return documents
