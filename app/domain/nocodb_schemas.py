from datetime import datetime
from typing import Optional, Any
from pydantic import BaseModel, Field

class UserDTO(BaseModel):
    id: int
    firebase_uid: str
    email: str
    display_name: Optional[str] = None

class TierDTO(BaseModel):
    id: int
    name: str
    max_concepts: int
    price_monthly: float
    is_active: bool

class SubscriptionDTO(BaseModel):
    id: int
    user_id: int
    tier_id: int
    status: str
    started_at: Optional[datetime] = None
    ends_at: Optional[datetime] = None
    
    @classmethod
    def from_nocodb(cls, data: dict) -> "SubscriptionDTO":
        """
        Map from NocoDB's internal representation to our DTO.
        NocoDB usually returns linked records as arrays of ids or objects,
        or we query with specific params. We assume we get 'users' and 'tiers' fields.
        """
        # Exctract link fields if they are present, sometimes they come as integer or dict
        def extract_id(val: Any) -> int:
            if isinstance(val, list) and len(val) > 0:
                val = val[0]
            if isinstance(val, dict):
                return val.get('id', 0)
            return int(val) if val else 0

        user_id = extract_id(data.get("users", 0)) or data.get("user_id", 0)
        tier_id = extract_id(data.get("tiers", 0)) or data.get("tier_id", 0)

        # parse dates safely
        started_at = data.get("started_at")
        ends_at = data.get("ends_at")

        return cls(
            id=data.get("id"),
            user_id=user_id,
            tier_id=tier_id,
            status=data.get("status", ""),
            started_at=datetime.fromisoformat(started_at.replace("Z", "+00:00")) if started_at else None,
            ends_at=datetime.fromisoformat(ends_at.replace("Z", "+00:00")) if ends_at else None,
        )

class SubscriptionCreateRequest(BaseModel):
    user_id: int
    tier_id: int
    status: str

    def to_nocodb(self) -> dict:
        """
        Map from our request DTO to NocoDB's internal structure.
        """
        return {
            "users": self.user_id,
            "tiers": self.tier_id,
            "status": self.status,
            # Let the DB set started_at if handled by default, or set it here if required.
        }
