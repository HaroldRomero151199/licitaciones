from typing import List
from app.infrastructure.nocodb.client import NocoDBClient
from app.domain.nocodb_schemas import SubscriptionDTO, SubscriptionCreateRequest

class SubscriptionService:
    def __init__(self, client: NocoDBClient):
        self.client = client

    async def create(self, request: SubscriptionCreateRequest) -> SubscriptionDTO:
        payload = request.to_nocodb()
        
        # We send a single object.
        created_data = await self.client.create_subscription(payload)
        
        if isinstance(created_data, list) and len(created_data) > 0:
            record = created_data[0]
        else:
            record = created_data

        return SubscriptionDTO.from_nocodb(record)
