import logging
from datetime import date
from typing import Optional

import httpx
from pydantic import ValidationError
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from app.domain.models import LicitacionResponse

logger = logging.getLogger(__name__)


class MercadoPublicoClient:
    BASE_URL = "https://api.mercadopublico.cl/servicios/v1/publico"

    def __init__(self, ticket: str, timeout: float = 30.0):
        self.ticket = ticket
        self.timeout = timeout
        self.client = httpx.AsyncClient(timeout=timeout)

    async def close(self):
        await self.client.aclose()

    @retry(
        stop=stop_after_attempt(5),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type((httpx.RequestError, httpx.HTTPStatusError)),
        reraise=True
    )
    async def _get(self, endpoint: str, params: dict) -> dict:
        params["ticket"] = self.ticket
        url = f"{self.BASE_URL}/{endpoint}"
        
        try:
            response = await self.client.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            return data
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error occurred: {e.response.status_code} - {e.response.text}")
            raise
        except httpx.RequestError as e:
            logger.error(f"Request error occurred: {e}")
            raise
        except Exception as e:
            logger.error(f"An unexpected error occurred: {e}")
            raise

    async def get_by_date(self, date_str: str) -> LicitacionResponse:
        """
        Get licitaciones by date.
        Date format: ddmmaaaa (e.g., 02022026)
        """
        params = {"fecha": date_str}
        data = await self._get("licitaciones.json", params)
        
        try:
            return LicitacionResponse(**data)
        except ValidationError as e:
            logger.error(f"Validation error for date {date_str}: {e}")
            raise

    async def get_by_code(self, code: str) -> LicitacionResponse:
        """
        Get licitacion details by code.
        """
        params = {"codigo": code}
        data = await self._get("licitaciones.json", params)
        
        try:
            return LicitacionResponse(**data)
        except ValidationError as e:
            logger.error(f"Validation error for code {code}: {e}")
            raise
