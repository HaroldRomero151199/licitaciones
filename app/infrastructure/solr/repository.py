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

    async def upsert_many(self, docs: List[Dict[str, Any]]) -> None:
        """
        Sube multiples documentos a Solr.
        Nota: pysolr.add es síncrono, pero lo envolvemos en una función async para cumplir con la interfaz.
        En un entorno de alta concurrencia, esto debería correrse en un thread pool si bloquea mucho, 
        pero para un proceso batch está bien.
        """
        if not docs:
            return

        try:
            # pysolr .add handles batches internally if needed, but we are passing a list.
            # commit=True forces a commit after adding.
            # Using commit=True inside the loop or after requires care. 
            # The requirement says "commit=True al final".
            # Pysolr's add method takes a list of docs.
            logger.info(f"Indexing {len(docs)} documents to Solr...")
            result = self.solr.add(docs, commit=True)
            logger.info(f"Solr response: {result}")
        except Exception as e:
            logger.error(f"Error indexing documents to Solr: {e}")
            raise
