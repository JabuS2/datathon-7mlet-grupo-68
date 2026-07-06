"""E8 — RBAC: a guarda `require_role` barra papéis fora do permitido (Etapa 8)."""
import pytest

from core.auth_dependencies import require_operador, require_role
from enums.usuario import TipoUsuario
from http_exceptions import Forbidden


class _User:
    def __init__(self, tipo: TipoUsuario):
        self.tipo = tipo


@pytest.mark.asyncio
async def test_operador_passes():
    user = _User(TipoUsuario.OPERADOR)
    assert await require_operador(user) is user


@pytest.mark.asyncio
async def test_demo_is_forbidden_from_operador_routes():
    with pytest.raises(Forbidden) as exc:
        await require_operador(_User(TipoUsuario.DEMO))
    assert exc.value.code == "ROLE_NOT_ALLOWED"


@pytest.mark.asyncio
async def test_require_role_accepts_multiple_roles():
    guard = require_role(TipoUsuario.OPERADOR, TipoUsuario.DEMO)
    user = await guard(_User(TipoUsuario.DEMO))
    assert user.tipo == TipoUsuario.DEMO
