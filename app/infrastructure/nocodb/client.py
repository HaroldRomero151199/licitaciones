import httpx
from typing import Any, Dict, Optional
from fastapi import HTTPException

from app.config import settings

class NocoDBClient:
    def __init__(self):
        self.base_url = settings.nocodb_base_url.rstrip('/')
        self.token = settings.nocodb_token
        self.headers = {
            "xc-token": self.token,
            "Content-Type": "application/json"
        }
        
    async def _request(self, method: str, table_id: str, endpoint: str = "", **kwargs) -> Any:
        url = f"{self.base_url}/api/v2/tables/{table_id}/records{endpoint}"
        async with httpx.AsyncClient() as client:
            try:
                response = await client.request(method, url, headers=self.headers, **kwargs)
                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError as e:
                # Provide a generic error from NocoDB
                raise HTTPException(
                    status_code=e.response.status_code, 
                    detail=f"NocoDB API error: {e.response.text}"
                )
            except httpx.RequestError as e:
                raise HTTPException(
                    status_code=500, 
                    detail=f"NocoDB connection error: {str(e)}"
                )

    async def get_users(self, limit: int = 100, offset: int = 0) -> Dict[str, Any]:
        params = {"limit": limit, "offset": offset}
        return await self._request("GET", settings.nocodb_table_id_users, params=params)

    async def get_user_by_email(self, email: str) -> Dict[str, Any]:
        params = {
            "where": f"(email,eq,{email})",
            "limit": 1
        }
        return await self._request("GET", settings.nocodb_table_id_users, params=params)
        
    async def get_tiers(self, limit: int = 100, offset: int = 0) -> Dict[str, Any]:
        params = {"limit": limit, "offset": offset}
        return await self._request("GET", settings.nocodb_table_id_tiers, params=params)
        
    async def get_subscription(self, record_id: int) -> Dict[str, Any]:
        return await self._request("GET", settings.nocodb_table_id_subscriptions, f"/{record_id}")

    async def get_subscriptions_by_user(self, user_id: int) -> Dict[str, Any]:
        params = {
            "where": f"(users_id,eq,{user_id})~and(status,eq,active)",
            "limit": 10
        }
        return await self._request("GET", settings.nocodb_table_id_subscriptions, params=params)
        
    async def create_subscription(self, payload: dict) -> Dict[str, Any]:
        # NocoDB expects an array or single object for inserting into table
        return await self._request("POST", settings.nocodb_table_id_subscriptions, json=payload)

    async def get_subscription_concepts(self, subscription_id: int, limit: int = 100, offset: int = 0) -> Dict[str, Any]:
        params = {
            "where": f"(subscriptions_id,eq,{subscription_id})",
            "limit": limit,
            "offset": offset
        }
        return await self._request("GET", settings.nocodb_table_id_subscription_concepts, params=params)

    async def get_subscription_concept(self, record_id: int) -> Dict[str, Any]:
        return await self._request("GET", settings.nocodb_table_id_subscription_concepts, f"/{record_id}")
        
    async def create_subscription_concept(self, payload: dict) -> Dict[str, Any]:
        return await self._request("POST", settings.nocodb_table_id_subscription_concepts, json=payload)

    async def delete_subscription_concept(self, record_id: int) -> Dict[str, Any]:
        return await self._request("DELETE", settings.nocodb_table_id_subscription_concepts, json=[{"Id": record_id}])

