from typing import List, Protocol
from datetime import date
from app.domain.models import Licitacion

class MercadoPublicoClientPort(Protocol):
    async def get_daily_list(self, target_date: date) -> List[Licitacion]:
        """Obtiene la lista de licitaciones de una fecha."""
        ...

    async def get_detail(self, code: str) -> Licitacion:
        """Obtiene el detalle de una licitación específica."""
        ...
