import logging
import time
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
import math

from starlette.concurrency import run_in_threadpool

from app.domain.ports import SolrTenderRepositoryPort
from app.infrastructure.mercadopublico.client import MercadoPublicoClient
from app.application.transformer_service import TenderTransformer
from app.domain.schemas import TenderIndexDoc

logger = logging.getLogger(__name__)

class TenderIngestionService:
    def __init__(self, mp_client: MercadoPublicoClient, solr_repo: SolrTenderRepositoryPort):
        self.mp_client = mp_client
        self.solr_repo = solr_repo
        self.batch_size = 50

    @staticmethod
    def chunk_list(data: List[Any], size: int) -> List[List[Any]]:
        """Splits a list into chunks of a given size."""
        return [data[i:i + size] for i in range(0, len(data), size)]

    @staticmethod
    def normalize_date(value: Any) -> Optional[str]:
        """
        Normalizes a date/datetime to ISO8601 UTC string (YYYY-MM-DDTHH:MM:SSZ).
        Handles None, strings, and datetime objects.
        If timezone is missing, assumes local/naive and appends 'Z' or converts to UTC representation.
        Solr STRICTLY requires 'Z' at the end for UTC dates if sending as string.
        """
        if not value:
            return None
        
        if isinstance(value, str):
            # Try to parse if it's a string to ensure standard format
            # Typical formats: "2026-02-16T15:00:00", "2026-02-16T15:00:00Z", "2026-02-16T15:00:00.000Z"
            if value.endswith("Z"):
                return value
            try:
                # If it looks like ISO but missing Z, append Z (assuming source is UTC-ish or Solr expects it so)
                # But MP usually sends local time in Chile. 
                # However, for string comparison purposes with Solr (which stores Z), 
                # we should just append Z if it's a valid iso string.
                # Validate simple ISO format
                datetime.fromisoformat(value) 
                return f"{value}Z"
            except ValueError:
                return value # Return as is if we can't parse, let Solr or comparison fail/handle it

        if isinstance(value, datetime):
            # Convert to UTC if it has tzinfo, else assume UTC or just format with Z
            if value.tzinfo is not None:
                # Convert to UTC
                value_utc = value.astimezone(timezone.utc)
                return value_utc.strftime("%Y-%m-%dT%H:%M:%SZ")
            else:
                # Naive, assume it's what we want to store + Z
                return value.strftime("%Y-%m-%dT%H:%M:%SZ")
                
        return str(value)

    async def ingest_actives(self) -> Dict[str, Any]:
        """Deprecated wrapper for backward compatibility or simple full ingestion."""
        # For now, we can redirect to delta 'activas' or keep old logic. 
        # Requirement says "wrapper ingest_actives_delta".
        return await self.ingest_actives_delta()

    async def ingest_actives_delta(self) -> Dict[str, Any]:
        """Wrapper to ingest active tenders using delta sync."""
        return await self.ingest_by_status_delta("activas")

    async def ingest_by_status_delta(self, status_filter: str) -> Dict[str, Any]:
        """
        Incremental ingestion (delta sync) by status.
        Status options: activas, publicada, cerrada, desierta, adjudicada, revocada, suspendida.
        """
        start_time = time.time()
        stats = {
            "status": "processing",
            "total_found_api": 0,
            "new_count": 0,
            "indexed_new": 0,
            "updated_count": 0,
            "skipped_count": 0,
            "errors_count": 0,
            "execution_time_ms": 0
        }

        try:
            logger.info(f"Starting delta ingestion for status='{status_filter}'...")
            
            # 1. Fetch from API
            try:
                response = await self.mp_client.get_by_status(status_filter)
                api_list = response.listado
            except Exception as e:
                logger.error(f"Failed to fetch list from MercadoPublico: {e}")
                stats["status"] = "error"
                stats["error_detail"] = f"API fetch failed: {str(e)}"
                return stats

            stats["total_found_api"] = len(api_list)
            logger.info(f"API returned {len(api_list)} items.")

            # 2. Build incoming map: {id: {status_code, closing_date}}
            incoming_map = {}
            for item in api_list:
                # Normalizamos fechas y status desde el listado
                # item.CodigoEstado is int
                # item.FechaCierre is datetime or None
                incoming_map[item.codigo_externo] = {
                    "status_code": item.codigo_estado,
                    "closing_date": self.normalize_date(item.fecha_cierre)
                }

            if not incoming_map:
                logger.info("No items to process.")
                stats["status"] = "ok"
                return stats

            all_ids = list(incoming_map.keys())

            # 3. Fetch current state from Solr (Chunks of 200)
            solr_state_map = {}
            id_chunks = self.chunk_list(all_ids, 200)
            
            for chunk in id_chunks:
                # fetch_min_fields_by_ids runs in threadpool ideally if blocking, 
                # but repo is sync. We should use run_in_threadpool.
                chunk_docs = await run_in_threadpool(
                    self.solr_repo.fetch_min_fields_by_ids, 
                    chunk
                )
                solr_state_map.update(chunk_docs)

            # 4. Compare and categorize
            new_ids = []
            updates_payload = []
            
            for doc_id, incoming_data in incoming_map.items():
                if doc_id not in solr_state_map:
                    # NEW
                    new_ids.append(doc_id)
                    stats["new_count"] += 1
                else:
                    # EXISTING - Check for changes
                    solr_doc = solr_state_map[doc_id]
                    
                    # Solr fields
                    # Solr might return list or scalar for pint/tdate fields depending on schema/pysolr
                    current_status_raw = solr_doc.get("status_code")
                    if isinstance(current_status_raw, list):
                        current_status_code = current_status_raw[0] if current_status_raw else None
                    else:
                        current_status_code = current_status_raw

                    # Incoming fields
                    new_status_code = incoming_data["status_code"]
                    
                    # Compare
                    # status_code is ONLY trigger for update
                    
                    # Ensure numeric comparison for status code (handle None/string from Solr)
                    try:
                        current_status_int = int(current_status_code) if current_status_code is not None else -1
                    except (ValueError, TypeError):
                        current_status_int = -1
                        
                    needs_update = False
                    update_doc = {"id": doc_id}
                    
                    if current_status_int != new_status_code:
                        # logger.info(f"Status change for {doc_id}: Solr={current_status_int} vs API={new_status_code}")
                        update_doc["status_code"] = {"set": new_status_code}
                        needs_update = True
                        
                    if needs_update:
                        updates_payload.append(update_doc)
                        # stats["updated_count"] += 1  <-- Moved to after successful update
                    else:
                        stats["skipped_count"] += 1          
            # 5. Process NEW items (Full Ingestion)
            if new_ids:
                logger.info(f"Processing {len(new_ids)} NEW items...")
                
                new_docs_batch = []
                
                for new_id in new_ids:
                    try:
                        detail_response = await self.mp_client.get_by_code(new_id)
                        if detail_response.listado:
                            licitacion = detail_response.listado[0]
                            doc_model = TenderTransformer.to_index_doc(licitacion)
                            new_docs_batch.append(doc_model.model_dump(mode='json'))
                        else:
                            logger.warning(f"No detail found for new item {new_id}")
                            stats["errors_count"] += 1
                    except Exception as e:
                        logger.error(f"Error fetching/transforming new item {new_id}: {e}")
                        stats["errors_count"] += 1
                    
                    # Flush batch to Solr periodically (e.g., every 50)
                    if len(new_docs_batch) >= 50:
                        try:
                            await run_in_threadpool(self.solr_repo.upsert_many, new_docs_batch)
                            stats["indexed_new"] += len(new_docs_batch)
                        except Exception as e:
                            logger.error(f"Error indexing batch of new items: {e}")
                            stats["errors_count"] += len(new_docs_batch)
                        new_docs_batch = []
                
                # Flush remaining
                if new_docs_batch:
                    try:
                        await run_in_threadpool(self.solr_repo.upsert_many, new_docs_batch)
                        stats["indexed_new"] += len(new_docs_batch)
                    except Exception as e:
                        logger.error(f"Error indexing final batch of new items: {e}")
                        stats["errors_count"] += len(new_docs_batch)

            # 6. Process UPDATED items (Atomic Updates)
            if updates_payload:
                logger.info(f"Processing {len(updates_payload)} updates...")
                # Batch atomic updates
                update_chunks = self.chunk_list(updates_payload, 500)
                for chunk in update_chunks:
                    try:
                        await run_in_threadpool(self.solr_repo.atomic_update_many, chunk)
                        stats["updated_count"] += len(chunk)
                    except Exception as e:
                        logger.error(f"Error sending batch updates: {e}")
                        stats["errors_count"] += len(chunk)

            stats["status"] = "ok"

        except Exception as e:
            logger.error(f"Critical error during delta ingestion: {e}")
            stats["status"] = "error"
            stats["error_detail"] = str(e)
        
        end_time = time.time()
        stats["execution_time_ms"] = int((end_time - start_time) * 1000)
        
        logger.info(f"Delta ingestion finished: {stats}")
        return stats
