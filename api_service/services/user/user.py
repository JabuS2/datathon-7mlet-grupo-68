from core.jwt_token import JwtToken
from db.unit_of_work import UnitOfWork
from http_exceptions import Conflict
from models.user import User
from schemas.token import TokenResponse
from schemas.user import UserCreate, UserLogin, UserResponse


class UserService:
    def __init__(self, uow: UnitOfWork, jwt: JwtToken):
        self.uow = uow
        self.jwt = jwt

    async def register(self, data: UserCreate) -> UserResponse:
        async with self.uow:
            existing = await self.uow.users.get_by_email(data.email)

            if existing:
                raise Conflict("Email já registrado", code="EMAIL_EXISTS")

            user = User(
                email=data.email,
                hashed_password=self.jwt.hash_password(data.password),
            )

            self.uow.users.add(user)

            return UserResponse.model_validate(user)

    async def login(self, data: UserLogin) -> TokenResponse:
        async with self.uow:
            user = await self.uow.users.get_by_email(data.email)

            if not user or not self.jwt.verify_password(
                data.password,
                user.hashed_password,
            ):
                raise Conflict("Email ou senha inválidos", code="INVALID_CREDENTIALS")

            token = self.jwt.create_access_token({"user_id": user.id})

            return TokenResponse(access_token=token, token_type="bearer")
