from typing import List
from fastapi import APIRouter, Depends, HTTPException

from app.domain.nocodb_schemas import TierDTO
from app.application.tier_service import TierService
from app.dependencies import get_tier_service, require_admin_token

router = APIRouter(prefix="/tiers", tags=["Tiers"], dependencies=[Depends(require_admin_token)])

@router.get("", response_model=List[TierDTO])
async def get_tiers(service: TierService = Depends(get_tier_service)):
    """
    Get list of tiers from NocoDB.
    
    Example:
        curl -X GET "http://localhost:8000/tiers" \\
             -H "X-ADMIN-TOKEN: your_admin_token"
    """
    try:
        return await service.get_all()
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
