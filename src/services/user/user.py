from sqlalchemy.ext.asyncio import AsyncSession

from src.core.jwt_token import JwtToken
from src.db.unit_of_work import UnitOfWork
from src.http import Conflict
from src.models.user import User
from src.repositories.user import UserRepository
from src.schemas.token import TokenResponse
from src.schemas.user import UserCreate, UserLogin, UserResponse


class UserService:
    def __init__(self, session: AsyncSession, repo: UserRepository, uow: UnitOfWork, jwt: JwtToken):
        self.session = session
        self.repo = repo
        self.uow = uow
        self.jwt = jwt

    async def register(self, data: UserCreate) -> UserResponse:
        async with self.uow:
            existing = await self.repo.get_by_email(data.email)
            if existing:
                raise Conflict("Email já registrado", code="EMAIL_EXISTS")

            user = User(
                email=data.email,
                hashed_password=self.jwt.hash_password(data.password)
            )

            await self.repo.add(user)
            return UserResponse.model_validate(user)
        
    async def login(self, data: UserLogin) -> TokenResponse:
        user = await self.repo.get_by_email(data.email)
        if not user or not self.jwt.verify_password(data.password, user.hashed_password):
            raise Conflict("Email ou senha inválidos", code="INVALID_CREDENTIALS")

        token = self.jwt.create_access_token({"user_id": user.id})
        return TokenResponse(access_token=token, token_type="bearer")