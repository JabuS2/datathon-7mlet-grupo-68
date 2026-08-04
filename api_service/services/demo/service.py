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
from schemas.cliente import (
    ClienteResponse,
    OnboardingRequest,
    OnboardingResponse,
    ProfileQuestions,
)
from services.demo.segments import compute_segments

# Faixa reservada de ids p/ perfis criados na vitrine (rastreáveis / purgáveis — LGPD).
DEMO_COD_BASE = 9_000_000


class OnboardingService:
    def __init__(self, uow: UnitOfWork, jwt: JwtToken):
        self.uow = uow
        self.jwt = jwt

    async def onboard(self, req: OnboardingRequest) -> OnboardingResponse:
        """Cadastro em uma etapa: cria conta E perfil. Usado pela API/scripts/testes."""
        async with self.uow:
            if await self.uow.users.get_by_email(req.email):
                raise Conflict("Email já registrado", code="EMAIL_EXISTS")

            cliente = await self._build_cliente(req)
            self.uow.clientes.add(cliente)

            user = User(
                email=req.email,
                hashed_password=self.jwt.hash_password(req.password),
                tipo=TipoUsuario.DEMO,
                cod_cliente=cliente.cod_cliente,
            )
            self.uow.users.add(user)
            await self.uow.session.flush()  # materializa user.id

            token = self.jwt.create_access_token({"user_id": user.id})
            return OnboardingResponse(
                access_token=token, cliente=ClienteResponse.model_validate(cliente)
            )

    async def complete_profile(self, user: User, req: ProfileQuestions) -> ClienteResponse:
        """Anexa um perfil de cliente a uma conta que **já existe** (cadastro em duas etapas).

        É o caminho do front: registrar → logar → responder as perguntas. Separar isso do
        `/onboarding` evita pedir email e senha de novo numa tela que é sobre perfil.
        """
        async with self.uow:
            fresh = await self.uow.users.get_by_id(user.id)
            if fresh is not None and fresh.cod_cliente is not None:
                raise Conflict("Sua conta já tem um perfil", code="PROFILE_EXISTS")

            cliente = await self._build_cliente(req)
            self.uow.clientes.add(cliente)
            if fresh is not None:
                fresh.cod_cliente = cliente.cod_cliente
                # a conta passa a ser um cliente da vitrine, não um operador
                fresh.tipo = TipoUsuario.DEMO
            await self.uow.session.flush()
            return ClienteResponse.model_validate(cliente)

    async def _build_cliente(self, req: ProfileQuestions) -> Cliente:
        """Sorteia o template, aplica as respostas e devolve o `Cliente` (sem persistir)."""
        template = await self.uow.clientes.pick_seed_template(req.segmento, req.idade)
        if template is None:
            raise Conflict("Sem dados de seed para gerar o perfil", code="NO_SEED_DATA")

        cod_cliente = self._next_demo_cod(
            await self.uow.clientes.max_cod_cliente(only_demo=True)
        )
        renda = (
            req.renda_estimada_anual_brl
            if req.renda_estimada_anual_brl is not None
            else template.renda_estimada_anual_brl
        )
        percentil = await self.uow.clientes.renda_percentil(renda)
        return self._from_template(template, req, cod_cliente, renda, percentil)

    @staticmethod
    def _next_demo_cod(max_demo: int | None) -> int:
        return max(DEMO_COD_BASE, (max_demo or DEMO_COD_BASE - 1) + 1)

    #: Flags que o visitante pode responder diretamente. As outras 21 vêm do template.
    ANSWERABLE_FLAGS = (
        "possui_cartao_credito",
        "possui_fundo_investimento",
        "possui_financiamento_imovel",
    )

    @classmethod
    def _from_template(
        cls,
        template: Cliente,
        req: ProfileQuestions,
        cod_cliente: int,
        renda: float | None,
        renda_percentil: float,
    ) -> Cliente:
        flags = {flag: getattr(template, flag) for flag in PRODUCT_FLAGS}
        # resposta explícita vence o template; omitida, o template decide
        for flag in cls.ANSWERABLE_FLAGS:
            answered = getattr(req, flag, None)
            if answered is not None:
                flags[flag] = answered

        tempo = (
            req.tempo_relacionamento_meses
            if req.tempo_relacionamento_meses is not None
            else template.tempo_relacionamento_meses
        )

        campos = {
            "cod_cliente": cod_cliente,
            "idade": req.idade,
            "segmento": req.segmento,
            "renda_estimada_anual_brl": renda,
            "tempo_relacionamento_meses": tempo,
            # o template já vem filtrado por `ind_ativo` (ver ClienteRepository):
            # perfil inativo não é elegível a quase nenhum braço e cai numa vitrine vazia
            "ind_ativo": template.ind_ativo,
            "estado": template.estado,
            "sexo": template.sexo,
            "evento_viagem_sintetico": template.evento_viagem_sintetico,
            "origem": OrigemCliente.DEMO,
            **flags,
        }
        # Recalculado, não copiado: as regras de segmento leem idade/renda/flags, que as
        # respostas acabaram de sobrescrever. Copiar do template produziria um perfil
        # contraditório (ex.: SEG-SENIOR num respondente de 25 anos).
        campos["segmentos_sinteticos"] = compute_segments(campos, renda_percentil)
        return Cliente(**campos)
