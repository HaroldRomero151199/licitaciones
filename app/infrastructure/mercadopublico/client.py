import logging
from datetime import date
from typing import Optional

import httpx
from pydantic import ValidationError
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from app.domain.schemas import LicitacionListResponse, LicitacionDetailResponse

logger = logging.getLogger(__name__)


class MercadoPublicoClient:
    def __init__(self, ticket: str, base_url: str, timeout: float = 30.0):
        self.ticket = ticket
        self.base_url = base_url.rstrip("/")
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
        url = f"{self.base_url}/{endpoint}"
        
        try:
            response = await self.client.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            return data
        except httpx.HTTPStatusError as e:
            error_data = None
            try:
                error_data = e.response.json()
                logger.error(f"HTTP error occurred: {e.response.status_code} - {error_data}")
            except Exception:
                logger.error(f"HTTP error occurred: {e.response.status_code} - {e.response.text}")
            
            raise
        except httpx.RequestError as e:
            logger.error(f"Request error occurred: {e}")
            raise
        except Exception as e:
            logger.error(f"An unexpected error occurred: {e}")
            raise

    async def get_by_date(self, date_str: str) -> LicitacionListResponse:
        """
        Get licitaciones by date.
        Date format: ddmmaaaa (e.g., 02022026)
        """
        params = {"fecha": date_str}
        data = await self._get("licitaciones.json", params)
        
        try:
            return LicitacionListResponse(**data)
        except ValidationError as e:
            logger.error(f"Validation error for date {date_str}: {e}")
            raise

    async def get_by_code(self, code: str) -> LicitacionDetailResponse:
        """
        Get licitacion details by code.
        """
        params = {"codigo": code}
        data = await self._get("licitaciones.json", params)
        
        try:
            return LicitacionDetailResponse(**data)
        except ValidationError as e:
            logger.error(f"Validation error for code {code}: {e}")
            raise

    async def get_raw_by_code(self, code: str) -> dict:
        """
        Get raw json licitacion details by code (no Pydantic validation).
        Useful for debugging full API response structure.
        """
        params = {"codigo": code}
        return await self._get("licitaciones.json", params)

    async def get_by_status(self, status: str) -> LicitacionListResponse:
        """
        Get licitaciones by status.
        Possible statuses: activas, publicada, cerrada, desierta, adjudicada, revocada, suspendida, todos.
        """
        params = {"estado": status}
        data = await self._get("licitaciones.json", params)
        
        try:
            return LicitacionListResponse(**data)
        except ValidationError as e:
            logger.error(f"Validation error for status {status}: {e}")
            raise
