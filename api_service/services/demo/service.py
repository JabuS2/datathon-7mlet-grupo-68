"""Onboarding da vitrine (§6): cadastro curto → perfil sintético por template + conta demo.

O visitante "vira mais uma linha do dataset": sorteamos uma linha real do seed que case com as
respostas, copiamos o vetor de contexto (24 flags `possui_*`, estado, tempo de relacionamento…)
como TEMPLATE — preservando as correlações reais entre produtos — e sobrescrevemos os campos
respondidos. Persistimos `cliente(origem='demo')` + `usuario(tipo='demo')` e devolvemos um token.
"""

from __future__ import annotations

from core.jwt_token import JwtToken
from db.unit_of_work import UnitOfWork
from enums.catalogo import OrigemCliente
from enums.usuario import TipoUsuario
from http_exceptions import Conflict
from models.cliente import PRODUCT_FLAGS, Cliente
from models.user import User
from schemas.cliente import ClienteResponse, OnboardingRequest, OnboardingResponse

# Faixa reservada de ids p/ perfis criados na vitrine (rastreáveis / purgáveis — LGPD).
DEMO_COD_BASE = 9_000_000


class OnboardingService:
    def __init__(self, uow: UnitOfWork, jwt: JwtToken):
        self.uow = uow
        self.jwt = jwt

    async def onboard(self, req: OnboardingRequest) -> OnboardingResponse:
        async with self.uow:
            if await self.uow.users.get_by_email(req.email):
                raise Conflict("Email já registrado", code="EMAIL_EXISTS")

            template = await self.uow.clientes.pick_seed_template(req.segmento, req.idade)
            if template is None:
                raise Conflict("Sem dados de seed para gerar o perfil", code="NO_SEED_DATA")

            cod_cliente = self._next_demo_cod(
                await self.uow.clientes.max_cod_cliente(only_demo=True)
            )
            cliente = self._from_template(template, req, cod_cliente)
            self.uow.clientes.add(cliente)

            user = User(
                email=req.email,
                hashed_password=self.jwt.hash_password(req.password),
                tipo=TipoUsuario.DEMO,
                cod_cliente=cod_cliente,
            )
            self.uow.users.add(user)
            await self.uow.session.flush()  # materializa user.id

            token = self.jwt.create_access_token({"user_id": user.id})
            return OnboardingResponse(
                access_token=token, cliente=ClienteResponse.model_validate(cliente)
            )

    @staticmethod
    def _next_demo_cod(max_demo: int | None) -> int:
        return max(DEMO_COD_BASE, (max_demo or DEMO_COD_BASE - 1) + 1)

    @staticmethod
    def _from_template(template: Cliente, req: OnboardingRequest, cod_cliente: int) -> Cliente:
        flags = {flag: getattr(template, flag) for flag in PRODUCT_FLAGS}
        renda = (
            req.renda_estimada_anual_brl
            if req.renda_estimada_anual_brl is not None
            else template.renda_estimada_anual_brl
        )
        return Cliente(
            cod_cliente=cod_cliente,
            idade=req.idade,  # sobrescrito pela resposta
            segmento=req.segmento,  # sobrescrito pela resposta
            renda_estimada_anual_brl=renda,
            tempo_relacionamento_meses=template.tempo_relacionamento_meses,
            ind_ativo=template.ind_ativo,
            estado=template.estado,
            sexo=template.sexo,
            segmentos_sinteticos=list(template.segmentos_sinteticos or []),
            evento_viagem_sintetico=template.evento_viagem_sintetico,
            origem=OrigemCliente.DEMO,
            **flags,
        )
