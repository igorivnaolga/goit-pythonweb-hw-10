import logging
from fastapi import APIRouter, status, BackgroundTasks, Request, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession

from src.schemas.users import UserResponse, UserCreate, TokenModel
from src.database.db import get_db
from src.services.users import UserService
from src.services.auth import auth_service


router = APIRouter(prefix="/auth", tags=["Auth"])
logger = logging.getLogger()


@router.post(
    "/signup/", response_model=UserResponse, status_code=status.HTTP_201_CREATED
)
async def signup(
    body: UserCreate,
    # background_task: BackgroundTasks,
    # request: Request,
    db: AsyncSession = Depends(get_db),
):
    user_service = UserService(db)
    exist_user = await user_service.get_user_by_email(body.email)
    if exist_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User with this email already exists",
        )

    # Hash password
    body.password = auth_service.get_password_hash(body.password)
    new_user = await user_service.create_user(body)
    return new_user


@router.post("/login", response_model=TokenModel)
async def login(
    body: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)
):
    user_service = UserService(db)
    user = await user_service.get_user_by_email(body.username)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email"
        )
    # if not user.confirmed_email:
    #     raise HTTPException(
    #         status_code=status.HTTP_401_UNAUTHORIZED, detail="Email not confirmed"
    # )
    if not auth_service.verify_password(body.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid password"
        )

    access_token = await auth_service.create_access_token(data={"sub": user.email})
    return {"access_token": access_token, "token_type": "bearer"}


# @router.post(
#     "/signup/", response_model=UserResponse, status_code=status.HTTP_201_CREATED
# )
# async def signup(
#     user: UserCreate,
#     # background_task: BackgroundTasks,
#     # request: Request,
#     db: AsyncSession = Depends(get_db),
# ):

#     user_service = UserService(db)
#     email_user = await user_service.get_user_by_email(user.email)

#     if email_user:
#         raise HTTPException(
#             status_code=status.HTTP_409_CONFLICT,
#             detail="User with this email already exist",
#         )
#     name_user = await user_service.get_user_by_name(user.username)

#     if name_user:
#         raise HTTPException(
#             status_code=status.HTTP_409_CONFLICT,
#             detail="User with this name already exist",
#         )

#     user.password = auth_service.get_password_hash(user.password)
#     new_user = await user_service.create_user(user)
#     # background_task.add_task(
#     #     send_email, new_user.email, new_user.username, str(request.base_url)
#     # )
#     return new_user


# @router.post("/login", response_model=TokenModel)
# async def login(
#     body: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)
# ):
#     user_service = UserService(db)
#     user = await user_service.get_user_by_name(body.username)
#     if user is None or not auth_service.verify_password(body.password, user.password):
#         raise HTTPException(
#             status_code=status.HTTP_401_UNAUTHORIZED,
#             detail="Invalid login or password ",
#         )
#     if not user.confirmed_email:
#         raise HTTPException(
#             status_code=status.HTTP_401_UNAUTHORIZED, detail="Email not confirmed"
#         )

#     # Generate JWT
#     access_token = await auth_service.create_access_token(data={"sub": user.email})
#     return {"access_token": access_token, "token_type": "bearer"}
