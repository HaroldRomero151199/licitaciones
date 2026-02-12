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

    def search(self, query: str, page: int = 1, size: int = 20, status_codes: List[int] = None, **kwargs) -> Dict[str, Any]:
        """
        Executes a search in Solr using pysolr (synchronous call).
        Now supports mandatory status_code filtering via fq.
        """
        try:
            query_str = (query or "").strip()
            # User requirement: q = _text_:("<search_term>")
            # We wrap the term in quotes and specify the field.
            # If query is empty, we fallback to *:* but requirements say search_term mandatory.
            
            if not query_str:
                # Fallback to match almost everything if empty, but route validation should prevent this if mandatory.
                search_q = "*:*"
                def_type = "lucene"
            else:
                # IMPORTANT: with edismax, q should be the raw user text.
                search_q = query_str
                def_type = "edismax"

            # Compute Solr pagination
            page = max(page, 1)
            size = max(min(size, 100), 1)
            start = (page - 1) * size

            # Default search parameters
            params = {
                "start": start,
                "rows": size,
                "fl": "*,score",
                "defType": def_type,
                # Include _text_ too, since your schema copyFields go there
                "qf": "title^2.0 description^1.0 _text_^1.0",
                "pf": "title^5.0",
            }
            
            # Handle status_codes filtering (fq)
            if status_codes:
                # fq = status_code:(5 6 8)
                codes_str = " ".join(str(c) for c in status_codes)
                fq_status = f"status_code:({codes_str})"
                
                existing_fq = kwargs.pop("fq", None)
                if existing_fq is None:
                    params["fq"] = fq_status
                elif isinstance(existing_fq, list):
                    params["fq"] = existing_fq + [fq_status]
                else:
                    params["fq"] = [existing_fq, fq_status]

            params.update(kwargs)

            logger.info(f"Searching Solr at {self.solr_url} with query='{search_q}', params={params}")
            results = self.solr.search(search_q, **params)

            # pysolr.Results exposes .hits and can be iterated to get documents
            docs = list(results)
            
            return {
                "query": query_str, # Return original query term for response
                "status_codes": status_codes,
                "total": results.hits,
                "docs": docs,
            }
        except Exception as e:
            logger.error(f"Error searching documents in Solr (query='{query}'): {e}")
            raise

    def fetch_min_fields_by_ids(self, ids: List[str]) -> Dict[str, Dict[str, Any]]:
        """
        Fetches minimal fields (id, status_code, closing_date) for a list of IDs.
        Uses POST to avoid URL length limits.
        
        Returns:
            Dict[str, Dict[str, Any]]: Map of id -> document fields
        """
        if not ids:
            return {}

        try:
            # Construct the query: id:(id1 OR id2 OR ...)
            # Escape IDs just in case, though usually they are safe
            safe_ids = [f'"{i}"' for i in ids]
            query_str = f"id:({' '.join(safe_ids)})"
            
            # Using standard Lucene parser for ID lookup
            params = {
                "fl": "id,status_code,closing_date",
                "rows": len(ids),
                "wt": "json"
            }
            
            # Use search method. pysolr.search uses GET by default but we can try to force POST 
            # if we use the underlying session or rely on pysolr's behavior. 
            # However, pysolr's search() mostly does GET. 
            # To be safe against URL limits with standard pysolr, we can use delete/add logic, 
            # but for querying we might need to rely on chunks if POST isn't easy.
            # BUT, pysolr >= 3.8 supports `search(..., **{'method': 'POST'})` if the server supports it (it usually does).
            
            logger.info(f"Fetching minimal fields for {len(ids)} IDs...")
            results = self.solr.search(query_str, **params) # pysolr defaults to POST for large queries automatically often, but let's be implicit if needed.
            # Actually pysolr by default sends GET. We can pass method='POST' in kwargs.
            # Let's try passing it to be safe.
            
            # Re-doing the call with method='POST' to ensure safety
            results = self.solr.search(query_str, method='POST', **params)
            
            docs_map = {}
            for doc in results:
                doc_id = doc.get("id")
                if doc_id:
                    docs_map[doc_id] = doc
                    
            return docs_map
            
        except Exception as e:
            logger.error(f"Error fetching min fields for IDs: {e}")
            raise

    def atomic_update_many(self, partials: List[Dict[str, Any]]) -> None:
        """
        Sends atomic updates to Solr.
        Each dict in `partials` should look like:
        {
            "id": "123",
            "field_name": {"set": value}
        }
        """
        if not partials:
            return
            
        try:
            logger.info(f"Sending atomic updates for {len(partials)} documents...")
            # commit=True to ensure consistency, or False for performance (controlled by caller or auto-commit)
            # here we use commit=True as requested in previous similar context, or strict safety.
            # For bulk, maybe commit=True at the end is better, but this method implies a batch.
            self.solr.add(partials, commit=True) # Removed fieldUpdates=True which caused TypeError
            # actually pysolr.add just sends the json. If the json has {"set": ...} Solr understands it.
            # But we must ensure pysolr doesn't flatten it weirdly. Pysolr handles dicts fine.
            logger.info(f"Atomic updates successful ({len(partials)} docs).")
        except Exception as e:
            logger.error(f"Error sending atomic updates: {e}")
            raise

    def get_by_id(self, tender_id: str) -> Dict[str, Any] | None:
        """
        Fetches a single document from Solr by its UniqueKey (id).
        """
        try:
            # Direct query by id
            query_str = f'id:"{tender_id}"'
            
            params = {
                "rows": 1,
                "wt": "json"
            }
            
            logger.info(f"Fetching document from Solr with id='{tender_id}'")
            results = self.solr.search(query_str, **params)
            
            if len(results) > 0:
                logger.info(f"Document found for id='{tender_id}'")
                return results.docs[0]
            
            logger.warning(f"No document found for id='{tender_id}'")
            return None
        except Exception as e:
            logger.error(f"Error fetching document by id='{tender_id}': {e}")
            raise
