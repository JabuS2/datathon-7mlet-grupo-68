from fastapi import APIRouter, Depends

from core.auth_dependencies import AuthDependencies
from core.jwt_token import JwtToken
from db.dependencies import get_uow
from db.unit_of_work import UnitOfWork
from schemas.token import TokenResponse
from schemas.user import UserCreate, UserLogin, UserResponse
from services.user.user import UserService

router = APIRouter()
auth = AuthDependencies()


@router.post(
    "/register", tags=["auth"], response_model=UserResponse, response_model_exclude_none=True
)
async def register_user(
    user: UserCreate,
    uow: UnitOfWork = Depends(get_uow),
):
    jwt = JwtToken()
    service = UserService(uow=uow, jwt=jwt)

    return await service.register(user)


@router.post(
    "/login", tags=["auth"], response_model=TokenResponse, response_model_exclude_none=True
)
async def login_user(user: UserLogin, uow: UnitOfWork = Depends(get_uow)):
    jwt = JwtToken()
    service = UserService(uow=uow, jwt=jwt)

    logged_user = await service.login(user)
    return logged_user


@router.get("/me", tags=["auth"], response_model=UserResponse, response_model_exclude_none=True)
async def me(current_user=Depends(auth.get_current_user)):
    return current_user
