from typing import List
from app.infrastructure.nocodb.client import NocoDBClient
from app.domain.nocodb_schemas import UserDTO

class UserService:
    def __init__(self, client: NocoDBClient):
        self.client = client

    async def get_all(self, limit: int = 100, offset: int = 0) -> List[UserDTO]:
        data = await self.client.get_users(limit=limit, offset=offset)
        records = data.get("list", [])
        return [UserDTO(**record) for record in records]
