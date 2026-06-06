from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.auth_dependencies import AuthDependencies
from src.core.jwt_token import JwtToken
from src.db.dependencies import get_db
from src.db.unit_of_work import UnitOfWork
from src.repositories.user import UserRepository
from src.schemas.token import TokenResponse
from src.schemas.user import UserCreate, UserLogin, UserResponse
from src.services.user.user import UserService

router = APIRouter()
auth = AuthDependencies()


@router.post("/register", tags=["auth"], response_model=UserResponse, response_model_exclude_none=True)
async def register_user(user: UserCreate, db: AsyncSession = Depends(get_db)):
    jwt = JwtToken()
    uow = UnitOfWork(db)
    repo = UserRepository(db)
    service = UserService(db, repo, uow, jwt)

    created_user = await service.register(user)
    return created_user

@router.post("/login", tags=["auth"], response_model=TokenResponse, response_model_exclude_none=True)
async def login_user(user: UserLogin, db: AsyncSession = Depends(get_db)):
    jwt = JwtToken()
    uow = UnitOfWork(db)
    repo = UserRepository(db)
    service = UserService(db, repo, uow, jwt)

    logged_user = await service.login(user)
    return logged_user

@router.get("/me", tags=["auth"], response_model=UserResponse, response_model_exclude_none=True)
async def me(current_user = Depends(auth.get_current_user)):
    return current_user