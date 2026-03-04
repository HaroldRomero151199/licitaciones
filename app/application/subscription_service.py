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
        
        # NocoDB POST only returns the new Id by default: {"Id": 4} or {"id": 4}
        if isinstance(created_data, list) and len(created_data) > 0:
            created_data = created_data[0]
            
        record_id = created_data.get("Id", created_data.get("id"))
        
        if not record_id:
            raise ValueError(f"Failed to get new record ID from NocoDB response: {created_data}")
            
        # Fetch the full record
        full_record = await self.client.get_subscription(record_id)

        return SubscriptionDTO(**full_record)
