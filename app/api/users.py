from typing import List
from fastapi import APIRouter, Depends, HTTPException

from app.domain.nocodb_schemas import UserDTO
from app.application.user_service import UserService
from app.dependencies import get_user_service, require_admin_token

router = APIRouter(prefix="/users", tags=["Users"], dependencies=[Depends(require_admin_token)])

@router.get("", response_model=List[UserDTO])
async def get_users(service: UserService = Depends(get_user_service)):
    """
    Get list of users from NocoDB.
    
    Example:
        curl -X GET "http://localhost:8000/users" \\
             -H "X-ADMIN-TOKEN: your_admin_token"
    """
    try:
        return await service.get_all()
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
