import logging
import time
from typing import Dict, Any, List
from datetime import datetime

from app.domain.ports import SolrTenderRepositoryPort
from app.infrastructure.mercadopublico.client import MercadoPublicoClient
from app.application.transformer_service import TenderTransformer
from app.domain.schemas import TenderIndexDoc

logger = logging.getLogger(__name__)

class ActiveTendersIngestionService:
    def __init__(self, mp_client: MercadoPublicoClient, solr_repo: SolrTenderRepositoryPort):
        self.mp_client = mp_client
        self.solr_repo = solr_repo
        self.batch_size = 200

    async def ingest_actives(self) -> Dict[str, Any]:
        """
        Orquesta la ingesta de licitaciones activas.
        1. Obtiene listado de activas
        2. Itera y obtiene detalle
        3. Transforma
        4. Upsert en Solr
        """
        start_time = time.time()
        stats = {
            "status": "processing",
            "total_actives_found": 0,
            "total_indexed": 0,
            "errors_count": 0,
            "execution_time_ms": 0
        }

        try:
            logger.info("Fetching active tenders list...")
            response = await self.mp_client.get_by_status("activas")
            actives_list = response.listado
            stats["total_actives_found"] = len(actives_list)
            logger.info(f"Found {len(actives_list)} active tenders. Starting ingestion...")

            batch: List[Dict[str, Any]] = []
            
            for item in actives_list:
                try:
                    # Traer detalle
                    detail_response = await self.mp_client.get_by_code(item.codigo_externo)
                    
                    if not detail_response.listado:
                        logger.warning(f"No detail found for {item.codigo_externo}")
                        continue
                        
                    licitacion = detail_response.listado[0]
                    
                    # Transformar
                    # map_to_index_doc returns a TenderIndexDoc Pydantic model
                    doc_model = TenderTransformer.to_index_doc(licitacion)
                    # Convert to dict for Solr
                    doc_dict = doc_model.model_dump(mode='json')
                    
                    batch.append(doc_dict)
                    
                    # Batch upsert
                    if len(batch) >= self.batch_size:
                        await self.solr_repo.upsert_many(batch)
                        stats["total_indexed"] += len(batch)
                        batch = []
                        
                except Exception as e:
                    logger.error(f"Error processing tender {item.codigo_externo}: {e}")
                    stats["errors_count"] += 1
                    continue
            
            # Process remaining batch
            if batch:
                await self.solr_repo.upsert_many(batch)
                stats["total_indexed"] += len(batch)

            stats["status"] = "ok"

        except Exception as e:
            logger.error(f"Critical error during active ingestion: {e}")
            stats["status"] = "error"
            stats["error_detail"] = str(e)
        
        end_time = time.time()
        stats["execution_time_ms"] = int((end_time - start_time) * 1000)
        
        logger.info(f"Ingestion finished: {stats}")
        return stats
