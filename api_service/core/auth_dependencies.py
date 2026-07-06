from typing import Annotated

import jwt
from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import ExpiredSignatureError, InvalidTokenError

from db.dependencies import get_uow
from db.unit_of_work import UnitOfWork
from enums.usuario import TipoUsuario
from http_exceptions import Forbidden, NotFound, Unauthorized
from models.user import User
from settings import settings

# auto_error=False: tratamos a ausência de credenciais nós mesmos, retornando 401 de forma
# determinística (independe da versão do FastAPI, que varia entre 401/403 no default).
bearer_scheme = HTTPBearer(auto_error=False)


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
            raise Unauthorized(code="INVALID_TOKEN", message="Token inválido")

        try:
            return int(sub)
        except ValueError as err:
            raise Unauthorized(code="INVALID_SUBJECT", message="Subject inválido no token") from err


async def get_current_user(
    token: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
    uow: Annotated[UnitOfWork, Depends(get_uow)],
) -> User:
    if token is None:
        raise Unauthorized(code="MISSING_TOKEN", message="Credenciais de autenticação ausentes")
    try:
        payload = AuthService.decode_token(token.credentials)
        user_id = AuthService.extract_user_id(payload)
    except ExpiredSignatureError as err:
        raise Unauthorized(code="TOKEN_EXPIRED", message="Token expirado") from err
    except InvalidTokenError as err:
        raise Unauthorized(code="INVALID_TOKEN", message="Token inválido") from err

    user = await uow.users.get_by_id(user_id)
    if not user:
        raise NotFound(message="Usuário não encontrado", code="USER_NOT_FOUND")
    return user


def require_role(*allowed: TipoUsuario):
    """Fábrica de dependência que barra usuários fora dos papéis permitidos (RBAC — Etapa 8).

    Ex.: `Depends(require_role(TipoUsuario.OPERADOR))` restringe a rota a operadores.
    """

    async def _guard(user: Annotated[User, Depends(get_current_user)]) -> User:
        if user.tipo not in allowed:
            raise Forbidden(
                message="Seu perfil não tem permissão para esta ação",
                code="ROLE_NOT_ALLOWED",
            )
        return user

    return _guard


# Guarda comum: rotas de governança/admin exigem operador (um cliente-demo nunca aprova política).
require_operador = require_role(TipoUsuario.OPERADOR)


class AuthDependencies:
    """Mantido por compatibilidade — delega para as funções de módulo."""

    get_current_user = staticmethod(get_current_user)
    require_operador = staticmethod(require_operador)
