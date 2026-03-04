from typing import List
from app.infrastructure.nocodb.client import NocoDBClient
from app.domain.nocodb_schemas import TierDTO

class TierService:
    def __init__(self, client: NocoDBClient):
        self.client = client

    async def get_all(self, limit: int = 100, offset: int = 0) -> List[TierDTO]:
        data = await self.client.get_tiers(limit=limit, offset=offset)
        records = data.get("list", [])
        return [TierDTO(**record) for record in records]
