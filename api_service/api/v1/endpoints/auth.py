import logging

from fastapi import APIRouter, Depends

from core.auth_dependencies import AuthDependencies
from core.jwt_token import JwtToken
from db.dependencies import get_uow
from db.unit_of_work import UnitOfWork
from schemas.token import TokenResponse
from schemas.user import UserCreate, UserLogin, UserResponse
from services.user.user import UserService

logger = logging.getLogger(__name__)
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

    result = await service.register(user)
    logger.info("user_registered", extra={"email": user.email})
    return result


@router.post(
    "/login", tags=["auth"], response_model=TokenResponse, response_model_exclude_none=True
)
async def login_user(user: UserLogin, uow: UnitOfWork = Depends(get_uow)):
    jwt = JwtToken()
    service = UserService(uow=uow, jwt=jwt)

    result = await service.login(user)
    logger.info("user_logged_in", extra={"email": user.email})
    return result


@router.get("/me", tags=["auth"], response_model=UserResponse, response_model_exclude_none=True)
async def me(current_user=Depends(auth.get_current_user)):
    return current_user
