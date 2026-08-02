from typing import Annotated

import jwt
from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import ExpiredSignatureError, InvalidTokenError

from db.dependencies import get_uow
from db.unit_of_work import UnitOfWork
from http_exceptions import Forbidden, NotFound, Unauthorized
from repositories.user import UserRepository
from settings import settings

bearer_scheme = HTTPBearer()


class AuthService:
    @staticmethod
    def decode_token(token: str) -> dict:
        return jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
            options={  # type: ignore[arg-type]
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
        except ValueError as err:
            raise Unauthorized(
                code="INVALID_SUBJECT",
                message="Subject inválido no token",
            ) from err


class AuthDependencies:
    def __init__(self):
        self.auth_service = AuthService()

    async def get_current_user(
        self,
        token: Annotated[HTTPAuthorizationCredentials, Depends(bearer_scheme)],
        uow: Annotated[UnitOfWork, Depends(get_uow)],
    ):
        try:
            payload = self.auth_service.decode_token(token.credentials)
            user_id = self.auth_service.extract_user_id(payload)

        except ExpiredSignatureError as err:
            raise Unauthorized(
                code="TOKEN_EXPIRED",
                message="Token expirado",
            ) from err

        except InvalidTokenError as err:
            raise Unauthorized(
                code="INVALID_TOKEN",
                message="Token inválido",
            ) from err

        repo = UserRepository(uow.session)
        user = await repo.get_by_id(user_id)

        if not user:
            raise NotFound(message="Usuário não encontrado", code="USER_NOT_FOUND")

        return user

    async def get_current_admin(
        self,
        token: Annotated[HTTPAuthorizationCredentials, Depends(bearer_scheme)],
        uow: Annotated[UnitOfWork, Depends(get_uow)],
    ):
        user = await self.get_current_user(token, uow)

        if not getattr(user, "is_admin", False):
            raise Forbidden(
                code="ADMIN_REQUIRED",
                message="Acesso restrito a administradores",
            )

        return user
