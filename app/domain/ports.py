from typing import List, Protocol, Dict, Any
from datetime import date
from app.domain.schemas import Licitacion, LicitacionItem

class MercadoPublicoClientPort(Protocol):
    async def get_daily_list(self, target_date: date) -> List[LicitacionItem]:
        """Obtiene la lista de licitaciones de una fecha."""
        ...

    async def get_detail(self, code: str) -> Licitacion:
        """Obtiene el detalle de una licitación específica."""
        ...

class SolrTenderRepositoryPort(Protocol):
    async def upsert_many(self, docs: List[dict]) -> None:
        """Sube multiples documentos al indice Solr.
        
        Args:
            docs: Lista de diccionarios o modelos convertidos a dict (DTOs para Solr).
        """
        ...

    def fetch_min_fields_by_ids(self, ids: List[str]) -> Dict[str, Dict[str, Any]]:
        """
        Fetches minimal fields (id, status_code, closing_date) for a list of IDs.
        Uses POST to avoid URL length limits.
        """
        ...

    def atomic_update_many(self, partials: List[Dict[str, Any]]) -> None:
        """
        Sends atomic updates to Solr.
        """
        ...

    def get_by_id(self, tender_id: str) -> Dict[str, Any] | None:
        """
        Fetches a single document by its id.
        """
        ...
