from datetime import datetime
from typing import Optional, Any
from pydantic import BaseModel, Field, ConfigDict

class BaseNocoSchema(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="ignore")

class UserDTO(BaseNocoSchema):
    id: int = Field(alias='Id')
    firebase_uid: str = Field(default="")
    email: str = Field(default="")
    display_name: Optional[str] = Field(default=None)

class TierDTO(BaseNocoSchema):
    id: int = Field(alias='Id')
    name: str = Field(default="")
    max_concepts: int = Field(default=0)
    price_monthly: float = Field(default=0.0)
    is_active: bool = Field(default=True)

class SubscriptionDTO(BaseNocoSchema):
    id: int = Field(alias='Id')
    user_id: int = Field(alias='users_id', default=0)
    tier_id: int = Field(alias='tiers_id', default=0)
    status: str = Field(default="")
    started_at: Optional[datetime] = Field(default=None)
    ends_at: Optional[datetime] = Field(default=None)

class SubscriptionCreateRequest(BaseModel):
    user_id: int
    tier_id: int
    status: str

    def to_nocodb(self) -> dict:
        """
        Map from our request DTO to NocoDB's internal structure for insertion.
        """
        return {
            "users_id": self.user_id,
            "tiers_id": self.tier_id,
            "status": self.status,
        }

class SubscriptionConceptDTO(BaseNocoSchema):
    id: int = Field(alias='Id')
    subscriptions_id: int = Field(default=0)
    concept: str = Field(default="")
    nc_order: Optional[str] = Field(default=None)

class SubscriptionConceptCreateRequest(BaseModel):
    subscriptions_id: int
    title: Optional[str] = None
    concept: str

    def to_nocodb(self) -> dict:
        """
        Map from our request DTO to NocoDB's internal structure for insertion.
        """
        return {
            "subscriptions_id": self.subscriptions_id,
            "concept": self.concept,
        }

class UserDetailDTO(BaseModel):
    user: UserDTO
    active_subscription: Optional[SubscriptionDTO] = None
    concepts: List[SubscriptionConceptDTO] = []
