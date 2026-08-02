"""Camada self-service do usuário logado (E12): perfil, histórico e checagem de posse.

Resolve o `cod_cliente` a partir do usuário autenticado (não do body) e garante que um `demo` só
opere sobre o próprio perfil/decisões. As decisões/feedback/reward em si continuam no
`DecisionService`; aqui ficam as leituras e as regras de posse.
"""

from __future__ import annotations

from uuid import UUID

from db.unit_of_work import UnitOfWork
from enums.usuario import TipoUsuario
from http_exceptions import Conflict, Forbidden, NotFound
from models.decisao import Decisao
from models.user import User
from schemas.cliente import ClienteResponse
from schemas.decisao import DecisaoResponse


class AccountService:
    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    async def profile(self, user: User) -> ClienteResponse:
        cod = self.require_cod_cliente(user)
        cliente = await self.uow.clientes.get_by_cod_cliente(cod)
        if cliente is None:
            raise NotFound("Perfil de cliente não encontrado", code="CLIENT_NOT_FOUND")
        return ClienteResponse.model_validate(cliente)

    async def decisions(self, user: User) -> list[DecisaoResponse]:
        cod = self.require_cod_cliente(user)
        rows = await self.uow.decisoes.list_by_cliente(cod)
        return [DecisaoResponse.model_validate(r) for r in rows]

    async def ensure_owns_decision(self, user: User, decision_id: UUID) -> Decisao:
        """Garante que a decisão pertence ao usuário (checagem de posse para feedback/reward)."""
        decision = await self.uow.decisoes.get_by_decision_id(decision_id)
        if decision is None:
            raise NotFound("Decisão não encontrada", code="DECISION_NOT_FOUND")
        if user.tipo == TipoUsuario.DEMO and decision.cod_cliente != user.cod_cliente:
            raise Forbidden("Esta decisão não pertence a você", code="NOT_DECISION_OWNER")
        return decision

    @staticmethod
    def require_cod_cliente(user: User) -> int:
        if user.cod_cliente is None:
            raise Conflict(
                "Sua conta não tem um perfil de cliente vinculado (use o cadastro da vitrine)",
                code="NO_CLIENT_PROFILE",
            )
        return user.cod_cliente
