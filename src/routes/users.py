from fastapi import APIRouter, Depends
from src.schemas.users import UserModel
from src.services.auth import Auth

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/me", response_model=UserModel)
async def get_me(user: UserModel = Depends(Auth.get_current_user)):
    return user
