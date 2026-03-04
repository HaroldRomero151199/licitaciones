from fastapi import APIRouter, Depends, HTTPException

from app.domain.nocodb_schemas import SubscriptionDTO, SubscriptionCreateRequest
from app.application.subscription_service import SubscriptionService
from app.dependencies import get_subscription_service, require_admin_token

router = APIRouter(prefix="/subscriptions", tags=["Subscriptions"], dependencies=[Depends(require_admin_token)])

@router.post("", response_model=SubscriptionDTO, status_code=201)
async def create_subscription(
    request: SubscriptionCreateRequest,
    service: SubscriptionService = Depends(get_subscription_service)
):
    """
    Create a new subscription in NocoDB.
    
    Example:
        curl -X POST "http://localhost:8000/subscriptions" \\
             -H "Content-Type: application/json" \\
             -H "X-ADMIN-TOKEN: your_admin_token" \\
             -d '{"user_id": 1, "tier_id": 2, "status": "active"}'
    """
    try:
        return await service.create(request)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
