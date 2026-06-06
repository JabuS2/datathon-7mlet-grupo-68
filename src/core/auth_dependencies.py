from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import ExpiredSignatureError, JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.dependencies import get_db
from src.repositories.user import UserRepository
from src.settings import settings
from src.http import Unauthorized, NotFound

bearer_scheme = HTTPBearer()


class AuthService:
    @staticmethod
    def decode_token(token: str) -> dict:
        return jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
            options={
                "require_exp": True,
                "require_iat": True,
                "require_sub": True,
            },
        )

    @staticmethod
    def extract_user_id(payload: dict) -> int:
        sub = payload.get("sub")

        if not sub:
            raise Unauthorized(
                code="INVALID_TOKEN",
                message="Token inválido",
            )

        try:
            return int(sub)
        except ValueError:
            raise Unauthorized(
                code="INVALID_SUBJECT",
                message="Subject inválido no token",
            )


class AuthDependencies:
    def __init__(self):
        self.auth_service = AuthService()

    async def get_current_user(
        self,
        token: Annotated[HTTPAuthorizationCredentials, Depends(bearer_scheme)],
        db: AsyncSession = Depends(get_db),
    ):
        try:
            payload = self.auth_service.decode_token(token.credentials)
            user_id = self.auth_service.extract_user_id(payload)

        except ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token expirado",
            )

        except JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token inválido",
            )

        repo = UserRepository(db)
        user = await repo.get_by_id(user_id)

        if not user:
            raise NotFound(
                message="Usuário não encontrado",
                code="USER_NOT_FOUND"
            )

        return user