from typing import List
from fastapi import APIRouter, Depends, HTTPException

from app.domain.nocodb_schemas import SubscriptionConceptDTO, SubscriptionConceptCreateRequest
from app.application.subscription_concept_service import SubscriptionConceptService
from app.dependencies import get_subscription_concept_service, require_admin_token

router = APIRouter(prefix="/subscription-concepts", tags=["Subscription Concepts"], dependencies=[Depends(require_admin_token)])

@router.post("", response_model=SubscriptionConceptDTO, status_code=201)
async def create_subscription_concept(
    request: SubscriptionConceptCreateRequest,
    service: SubscriptionConceptService = Depends(get_subscription_concept_service)
):
    """
    Create a new subscription concept in NocoDB.
    
    Example:
        curl -X POST "http://localhost:8000/subscription-concepts" \
             -H "Content-Type: application/json" \
             -H "X-ADMIN-TOKEN: your_admin_token" \
             -d '{"subscriptions_id": 1, "concept": "Example Concept"}'
    """
    try:
        return await service.create(request)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/subscription/{subscription_id}", response_model=List[SubscriptionConceptDTO])
async def get_subscription_concepts_by_subscription(
    subscription_id: int,
    service: SubscriptionConceptService = Depends(get_subscription_concept_service)
):
    """
    Get list of subscription concepts from NocoDB for a specific subscription.
    
    Example:
        curl -X GET "http://localhost:8000/subscription-concepts/subscription/1" \
             -H "X-ADMIN-TOKEN: your_admin_token"
    """
    try:
        return await service.get_all_by_subscription(subscription_id)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{concept_id}", status_code=204)
async def delete_subscription_concept(
    concept_id: int,
    service: SubscriptionConceptService = Depends(get_subscription_concept_service)
):
    """
    Delete a subscription concept from NocoDB.
    
    Example:
        curl -X DELETE "http://localhost:8000/subscription-concepts/1" \
             -H "X-ADMIN-TOKEN: your_admin_token"
    """
    try:
        await service.delete(concept_id)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
