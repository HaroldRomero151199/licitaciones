from typing import List, Protocol
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
