from datetime import date
from math import ceil
from typing import Any, Dict, List

from fastapi import APIRouter, Depends, Query
from starlette.concurrency import run_in_threadpool

from app.application.transformer_service import TenderTransformer
from app.infrastructure.solr.repository import SolrTenderRepository
from app.dependencies import get_solr_repository
from app.domain.schemas import TenderSummaryDTO

router = APIRouter()

@router.get("/")
async def root():
    return {"message": "Mercado Público Search Ingestor Active"}

@router.get("/search")
async def search(
    q: str,
    page: int = Query(1, ge=1, description="Page number (starting from 1)"),
    size: int = Query(20, ge=1, le=100, description="Page size (number of items per page)"),
    solr_repo: SolrTenderRepository = Depends(get_solr_repository),
):
    """
    Search endpoint backed by Solr that returns a paginated list of TenderSummaryDTO
    ready for frontend consumption.
    """
    # Run the blocking Solr call in a thread pool so the event loop is not blocked
    raw_result: Dict[str, Any] = await run_in_threadpool(solr_repo.search, q, page, size)

    dtos: List[TenderSummaryDTO] = [
        TenderTransformer.solr_doc_to_summary_dto(doc)
        for doc in raw_result.get("docs", [])
    ]

    total: int = raw_result.get("total", len(dtos))
    total_pages = ceil(total / size) if total > 0 else 1

    return {
        "query": raw_result.get("query", q),
        "page": page,
        "size": size,
        "total": total,
        "totalPages": total_pages,
        "items": dtos,
    }
