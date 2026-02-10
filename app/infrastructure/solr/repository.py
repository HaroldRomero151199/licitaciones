import logging
import pysolr
from typing import List, Dict, Any
from app.config import settings

logger = logging.getLogger(__name__)

class SolrTenderRepository:
    def __init__(self, base_url: str, core: str, username: str = None, password: str = None, timeout: int = 10):
        self.solr_url = f"{base_url.rstrip('/')}/{core}"
        self.username = username
        self.password = password
        self.timeout = timeout
        
        # Configure auth
        auth = None
        if username and password:
            auth = (username, password)
            
        self.solr = pysolr.Solr(
            self.solr_url, 
            always_commit=False, 
            timeout=timeout,
            auth=auth
        )
        logger.info(f"Solr Repository initialized at {self.solr_url} (Auth: {'Yes' if auth else 'No'})")

    def upsert_many(self, docs: List[Dict[str, Any]]) -> None:
        """
        Upserts multiple documents into Solr using pysolr (synchronous call).
        Intended to be executed in a thread pool from async code.
        """
        if not docs:
            return

        try:
            logger.info(f"Indexing {len(docs)} documents to Solr...")
            result = self.solr.add(docs, commit=True)
            logger.info(f"Solr response: {result}")
        except Exception as e:
            logger.error(f"Error indexing documents to Solr: {e}")
            raise

    def search(self, query: str, page: int = 1, size: int = 20, **kwargs) -> Dict[str, Any]:
        """
        Executes a search in Solr using pysolr (synchronous call).
        The `query` argument is treated as free text and searched mainly
        in `title` and `description` fields using the edismax parser, with
        additional boosting on `title`. If the query is empty or `*:*`, a
        match-all query is executed using the standard Lucene parser.
        """
        try:
            query_str = (query or "").strip()
            is_match_all = not query_str or query_str == "*:*"

            # Compute Solr pagination
            page = max(page, 1)
            size = max(size, 1)
            start = (page - 1) * size

            # Default search parameters:
            # - for free-text queries: edismax with boosting on title
            # - for match-all: standard Lucene parser
            params = {
                "start": start,
                "rows": size,
                "fl": "*,score",
                "defType": "edismax" if not is_match_all else "lucene",
                "qf": "title^2.0 description^1.0",
                "pf": "title^5.0",
            }
            params.update(kwargs)

            search_q = "*:*" if is_match_all else query_str

            logger.info(f"Searching Solr at {self.solr_url} with query='{search_q}', params={params}")
            results = self.solr.search(search_q, **params)

            # pysolr.Results exposes .hits and can be iterated to get documents
            docs = list(results)
            return {
                "query": search_q,
                "total": results.hits,
                "docs": docs,
            }
        except Exception as e:
            logger.error(f"Error searching documents in Solr (query='{query}'): {e}")
            raise
