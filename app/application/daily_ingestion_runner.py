import asyncio
import logging
import time
from datetime import datetime, timezone
from typing import Dict, Any, List

from app.application.active_ingestion_service import TenderIngestionService
from app.domain.schemas import LicitacionEstado

logger = logging.getLogger(__name__)

class DailyIngestionRunner:
    def __init__(self, ingestion_service: TenderIngestionService):
        self.ingestion_service = ingestion_service
        self._lock = asyncio.Lock()

    async def run_daily_sequence(self) -> Dict[str, Any]:
        """
        Runs the daily ingestion sequence for all statuses.
        Prevent concurrent runs using a lock.
        """
        if self._lock.locked():
            raise RuntimeError("Daily ingestion already running")

        async with self._lock:
            start_time = datetime.now(timezone.utc)
            logger.info(f"Starting daily ingestion sequence at {start_time.isoformat()}")
            
            # Order strictly as requested
            status_order = [
                LicitacionEstado.activas,
                LicitacionEstado.publicada,
                LicitacionEstado.cerrada,
                LicitacionEstado.desierta,
                LicitacionEstado.adjudicada,
                LicitacionEstado.revocada,
                LicitacionEstado.suspendida
            ]

            runs_results = []
            param_status = "ok"

            for status_enum in status_order:
                status_str = status_enum.value
                run_entry = {
                    "estado": status_str,
                    "ok": False
                }
                
                try:
                    logger.info(f"Starting ingestion for status: {status_str}")
                    # Call the existing delta method
                    result = await self.ingestion_service.ingest_by_status_delta(status_str)
                    
                    # Check if result indicates success (the service returns a dict with 'status')
                    if result.get("status") == "error":
                        run_entry["ok"] = False
                        run_entry["error"] = result.get("error_detail", "Unknown error from service")
                        param_status = "partial_error"
                    else:
                        run_entry["ok"] = True
                        run_entry["result"] = result

                except Exception as e:
                    logger.error(f"Exception during ingestion of {status_str}: {e}", exc_info=True)
                    run_entry["ok"] = False
                    run_entry["error"] = str(e)
                    param_status = "partial_error"
                
                runs_results.append(run_entry)

            finish_time = datetime.now(timezone.utc)
            
            # Determine final status
            # If all failed? -> error
            # If some failed? -> partial_error
            # If all ok? -> ok
            all_ok = all(r["ok"] for r in runs_results)
            all_failed = all(not r["ok"] for r in runs_results)
            
            if all_ok:
                final_status = "ok"
            elif all_failed:
                final_status = "error"
            else:
                final_status = "partial_error"

            summary = {
                "status": final_status,
                "started_at": start_time.isoformat(),
                "finished_at": finish_time.isoformat(),
                "runs": runs_results
            }
            
            logger.info(f"Daily ingestion sequence finished with status: {final_status}")
            return summary
