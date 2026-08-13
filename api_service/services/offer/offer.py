from __future__ import annotations

import logging

from db.unit_of_work import UnitOfWork
from models.cliente import Cliente
from models.feedback import FeedbackEvent
from models.user import User
from schemas.cliente import ClienteResponse
from schemas.feedback import FeedbackCreate, FeedbackResponse
from schemas.interesse import InteresseResponse
from schemas.offer import OfferResponse
from schemas.profile import ProfileUpdate
from services.account.service import AccountService
from services.bandit.client import BanditClient
from settings import settings

logger = logging.getLogger(__name__)


class OfferService:
    """Regras de ofertas: ranquear ofertas do usuário e aplicar feedback.

    O contexto do bandit vem do `Cliente` vinculado à conta (`users.cod_cliente`) — a mesma
    entidade que `Decisao`/`Recompensa` referenciam, para que a trilha auditável consiga ligar
    uma decisão ao perfil que a gerou. Contas sem cliente vinculado recebem
    `409 NO_CLIENT_PROFILE`; o caminho para ganhar um perfil é o cadastro da vitrine
    (`POST /onboarding`). O estado do modelo vive no model_service; aqui só orquestramos.
    """

    def __init__(self, uow: UnitOfWork, model_client: BanditClient):
        self.uow = uow
        self.model_client = model_client

    async def _require_cliente(self, user: User) -> Cliente:
        """Lê o cliente do usuário (deve ser chamado dentro de ``async with self.uow``)."""
        cod = AccountService.require_cod_cliente(user)
        cliente = await self.uow.clientes.get_by_cod_cliente(cod)
        if cliente is None:
            raise AccountService.no_client_profile()
        return cliente

    async def _resolve_context(self, user: User) -> tuple[dict, list[str]]:
        cliente = await self._require_cliente(user)
        return cliente.to_context(), list(cliente.segmentos_sinteticos)

    async def list_offers(
        self, user: User, algorithm: str | None = None, top: int | None = None
    ) -> list[OfferResponse]:
        """Vitrine do cliente: o ranking **completo** do modelo, marcando o que já está na
        carteira.

        Antes eu excluía os adquiridos do `/rank`. Com 10 braços no catálogo e a
        elegibilidade filtrando para ~6, bastavam poucos cliques para a vitrine esvaziar — e
        uma tela vazia parece modelo quebrado, não catálogo esgotado. O ranking segue
        completo; quem decide o que fazer com o já adquirido é a apresentação.
        """
        async with self.uow:
            features, segments = await self._resolve_context(user)
            ja_adquiridas = {arm for arm, _, _ in await self.uow.feedback.clicked_arms(user.id)}
        algo = algorithm or settings.DEFAULT_ALGORITHM

        result = await self.model_client.rank(algo, features, segments, top)
        offers = [
            OfferResponse(
                arm_id=r["arm_id"],
                rank=r["rank"],
                score=r["score"],
                category=r["category"],
                product_name=r["product_name"],
                description=r["description"],
                valor_total=r.get("valor_total"),
                desconto_pct=r.get("desconto_pct"),
                valor_final=r.get("valor_final"),
                ja_adquirida=r["arm_id"] in ja_adquiridas,
            )
            for r in result["ranked"]
        ]
        logger.info(
            "offers_listed",
            extra={
                "user_id": user.id,
                "cod_cliente": user.cod_cliente,
                "algorithm": result.get("algorithm", algo),
                "count": len(offers),
                "top_arm": offers[0].arm_id if offers else None,
            },
        )
        return offers

    async def submit_feedback(self, user: User, data: FeedbackCreate) -> FeedbackResponse:
        """Registra o clique, debita o produto do saldo e realimenta o modelo.

        O débito **não** condiciona o aprendizado: se o saldo não cobrir, o interesse é
        registrado do mesmo jeito e o modelo aprende. Bloquear o feedback por falta de saldo
        faria o bandit parar de aprender justamente com quem mais clica.
        """
        reward = 1.0 if data.clicked else 0.0
        algo = data.algorithm or settings.DEFAULT_ALGORITHM
        debitado = 0.0
        insuficiente = False

        async with self.uow:
            features, segments = await self._resolve_context(user)
            self.uow.feedback.add(
                FeedbackEvent(
                    user_id=user.id,
                    arm_id=data.arm_id,
                    algorithm=algo,
                    clicked=data.clicked,
                    reward=reward,
                )
            )

            if data.clicked:
                # preço do CATÁLOGO, não do corpo da requisição
                oferta = await self.uow.ofertas.get_by_arm_id(data.arm_id)
                preco = (oferta.valor_final if oferta else None) or 0.0
                conta = await self.uow.users.get_by_id(user.id)
                saldo = (conta.saldo_ficticio if conta else None) or 0.0
                if preco > 0 and conta is not None:
                    if saldo >= preco:
                        conta.saldo_ficticio = round(saldo - preco, 2)
                        debitado = preco
                    else:
                        insuficiente = True
                saldo_final = conta.saldo_ficticio if conta else None
            else:
                conta = await self.uow.users.get_by_id(user.id)
                saldo_final = conta.saldo_ficticio if conta else None

        # propaga o feedback ao modelo (recalcula as próximas ofertas do usuário)
        await self.model_client.update(algo, data.arm_id, reward, features, segments)

        logger.info(
            "feedback_submitted",
            extra={
                "user_id": user.id,
                "cod_cliente": user.cod_cliente,
                "arm_id": data.arm_id,
                "clicked": data.clicked,
                "reward": reward,
                "algorithm": algo,
                "valor_debitado": debitado,
                "saldo_insuficiente": insuficiente,
            },
        )
        return FeedbackResponse(
            arm_id=data.arm_id,
            clicked=data.clicked,
            reward=reward,
            algorithm=algo,
            status="applied",
            valor_debitado=debitado,
            saldo_ficticio=saldo_final,
            saldo_insuficiente=insuficiente,
        )

    async def list_interests(self, user: User) -> list[InteresseResponse]:
        """A carteira: ofertas em que o usuário clicou, enriquecidas pelo catálogo.

        Sem tabela própria — deriva de `feedback_events`, o mesmo log que alimenta o modelo.
        Assim o que a tela mostra e o que o bandit aprendeu não podem divergir.
        """
        async with self.uow:
            cliques = await self.uow.feedback.clicked_arms(user.id)
            if not cliques:
                return []
            ofertas = {o.arm_id: o for o in await self.uow.ofertas.get_all()}
            itens = []
            for arm_id, n, ultimo in cliques:
                oferta = ofertas.get(arm_id)
                if oferta is None:
                    continue  # braço saiu do catálogo: não inventamos nome
                itens.append(
                    InteresseResponse(
                        arm_id=arm_id,
                        product_name=oferta.product_name,
                        description=oferta.description,
                        category=oferta.category,
                        cliques=n,
                        ultimo_clique=ultimo,
                    )
                )
            return itens

    async def update_profile(self, user: User, data: ProfileUpdate) -> ClienteResponse:
        """Atualização parcial do contexto do próprio cliente. Campos omitidos não mudam."""
        async with self.uow:
            cliente = await self._require_cliente(user)
            for field, value in data.model_dump(exclude_unset=True).items():
                setattr(cliente, field, value)
            await self.uow.session.flush()
            response = ClienteResponse.model_validate(cliente)
        response.saldo_ficticio = user.saldo_ficticio
        return response
