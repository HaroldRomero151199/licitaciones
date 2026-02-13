from datetime import date
from math import ceil
from typing import Any, Dict, List

from fastapi import APIRouter, Depends, Query, HTTPException
from starlette.concurrency import run_in_threadpool

from app.application.transformer_service import TenderTransformer
from app.infrastructure.solr.repository import SolrTenderRepository
from app.dependencies import get_solr_repository, require_admin_token
from app.domain.schemas import TenderSummaryDTO

router = APIRouter(dependencies=[Depends(require_admin_token)])

@router.get("/")
async def root():
    return {"message": "Mercado Público Search Ingestor Active"}

@router.get("/tenders/{tender_id}", response_model=TenderSummaryDTO)
async def get_tender_by_id(
    tender_id: str,
    solr_repo: SolrTenderRepository = Depends(get_solr_repository),
):
    """
    Get a single tender by its ID from Solr.
    """
    doc = await run_in_threadpool(solr_repo.get_by_id, tender_id)
    
    if not doc:
        raise HTTPException(status_code=404, detail=f"Tender with id {tender_id} not found")
        
    return TenderTransformer.solr_doc_to_summary_dto(doc)

@router.get("/search")
async def search(
    search_term: str = Query(..., min_length=1, description="Term to search in title/description"),
    status_codes: List[int] = Query(..., min_length=1, description="List of status codes to filter by"),
    page: int = Query(1, ge=1, description="Page number (starting from 1)"),
    size: int = Query(20, ge=1, le=100, description="Page size (number of items per page)"),
    solr_repo: SolrTenderRepository = Depends(get_solr_repository),
):
    """
    Search endpoint backed by Solr that returns a paginated list of TenderSummaryDTO.
    Requires search_term and status_codes.
    """
    # Run the blocking Solr call in a thread pool so the event loop is not blocked
    # search_term maps to query argument in repo
    raw_result: Dict[str, Any] = await run_in_threadpool(
        solr_repo.search, 
        query=search_term, 
        page=page, 
        size=size,
        status_codes=status_codes
    )

    dtos: List[TenderSummaryDTO] = [
        TenderTransformer.solr_doc_to_summary_dto(doc)
        for doc in raw_result.get("docs", [])
    ]

    total: int = raw_result.get("total", len(dtos))
    total_pages = ceil(total / size) if total > 0 else 1

    return {
        "query": raw_result.get("query", search_term),
        "status_codes": raw_result.get("status_codes", status_codes),
        "page": page,
        "size": size,
        "total": total,
        "totalPages": total_pages,
        "items": dtos,
    }
