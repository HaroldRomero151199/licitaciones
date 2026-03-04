from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query

from app.domain.nocodb_schemas import UserDTO, UserDetailDTO
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

@router.get("/by-email", response_model=UserDetailDTO)
async def get_user_by_email(
    email: str = Query(..., description="The user's email address"),
    service: UserService = Depends(get_user_service)
):
    """
    Get user details by email, including their active subscription and associated concepts.
    
    Example:
        curl -X GET "http://localhost:8000/users/by-email?email=test@example.com" \
             -H "X-ADMIN-TOKEN: your_admin_token"
    """
    try:
        return await service.get_user_details_by_email(email)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
