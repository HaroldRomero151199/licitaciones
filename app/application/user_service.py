from typing import List
from fastapi import HTTPException
from app.infrastructure.nocodb.client import NocoDBClient
from app.domain.nocodb_schemas import UserDTO, UserDetailDTO, SubscriptionDTO, SubscriptionConceptDTO

class UserService:
    def __init__(self, client: NocoDBClient):
        self.client = client

    async def get_all(self, limit: int = 100, offset: int = 0) -> List[UserDTO]:
        data = await self.client.get_users(limit=limit, offset=offset)
        records = data.get("list", [])
        return [UserDTO(**record) for record in records]

    async def get_user_details_by_email(self, email: str) -> UserDetailDTO:
        # 1. Get user by email
        user_data = await self.client.get_user_by_email(email)
        user_records = user_data.get("list", [])
        if not user_records:
            raise HTTPException(status_code=404, detail="User not found")
            
        user_dto = UserDTO(**user_records[0])
        
        # 2. Get active subscription
        sub_data = await self.client.get_subscriptions_by_user(user_dto.id)
        sub_records = sub_data.get("list", [])
        
        active_sub_dto = None
        concepts_dtos = []
        
        if sub_records:
            # Take the first one (we filtered by status=active in the client)
            # You could also sort them if needed, but 'list' usually returns latest first if configured in NocoDB
            active_sub_dto = SubscriptionDTO(**sub_records[0])
            
            # 3. Get concepts for this subscription
            concepts_data = await self.client.get_subscription_concepts(active_sub_dto.id)
            concepts_records = concepts_data.get("list", [])
            concepts_dtos = [SubscriptionConceptDTO(**c) for c in concepts_records]
            
        return UserDetailDTO(
            user=user_dto,
            active_subscription=active_sub_dto,
            concepts=concepts_dtos
        )
