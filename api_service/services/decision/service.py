"""Serviço de serving: liga o engine do bandit (E6) ao banco (E4) e grava o log auditável (E5).

Fluxo por endpoint:
  /decide   → escolhe braço, persiste `Decisao` + `EventoImpressao(impression)`.
  /showcase → ranqueia a vitrine (somente leitura, sem persistir).
  /feedback → registra `EventoImpressao(click)`.
  /reward   → aplica a recompensa composta ao `EstadoBraco` (aprendizado) e grava `Recompensa`.
"""

from __future__ import annotations

import math
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from db.unit_of_work import UnitOfWork
from enums.decisao import StatusRecompensa, TipoEvento
from http_exceptions import Conflict, NotFound
from models.decisao import Decisao
from models.estado_braco import EstadoBraco
from models.evento_impressao import EventoImpressao
from models.recompensa import Recompensa
from schemas.decisao import (
    DecideResponse,
    FeedbackResponse,
    OfertaRankeada,
    RewardResponse,
    ShowcaseResponse,
)
from services.bandit.policies import build_policy
from services.bandit.state import ArmState
from services.decision.runtime import get_runtime


def _finite(value: float) -> float:
    """Evita inf/nan no JSON (ex.: score de cold-start do UCB)."""
    return value if math.isfinite(value) else 1e9


def _client_to_dict(cliente) -> dict[str, Any]:
    return {col.name: getattr(cliente, col.name) for col in cliente.__table__.columns}


def _orm_to_state(orm: EstadoBraco) -> ArmState:
    return ArmState(
        arm_id=orm.arm_id,
        alpha=orm.alpha,
        beta=orm.beta,
        n_pulls=orm.n_pulls,
        sum_reward=orm.sum_reward,
        A=orm.A,
        b=orm.b,
    )


class DecisionService:
    def __init__(self, uow: UnitOfWork):
        self.uow = uow
        self.rt = get_runtime()

    # ── /decide ──────────────────────────────────────────────────
    async def decide(self, cod_cliente: int, channel) -> DecideResponse:
        async with self.uow:
            client = await self._require_client(cod_cliente)
            policy = await self._require_active_policy()
            states = [
                _orm_to_state(s)
                for s in await self.uow.estados_braco.list_by_policy(policy.policy_id)
            ]
            pol = build_policy(
                policy.algorithm, dimension=self.rt.stats.dimension, hyperparams=policy.hyperparams
            )

            decision = self.rt.engine.decide(_client_to_dict(client), pol, states)
            if decision is None:
                raise Conflict("Nenhuma oferta elegível para o cliente", code="NO_ELIGIBLE_ARM")

            dec = Decisao(
                cod_cliente=cod_cliente,
                policy_version=policy.policy_id,
                chosen_arm_id=decision.arm_id,
                channel=channel,
                context=decision.context,
                reason_codes=decision.reason_codes,
                score=_finite(float(decision.score)),
            )
            self.uow.decisoes.add(dec)
            await self.uow.session.flush()  # materializa decision_id (default uuid4)
            self.uow.eventos_impressao.add(
                EventoImpressao(decision_id=dec.decision_id, type=TipoEvento.IMPRESSION)
            )

            offer = self.rt.offers_by_id[decision.arm_id]
            return DecideResponse(
                decision_id=dec.decision_id,
                arm_id=decision.arm_id,
                product_name=offer["product_name"],
                description=offer["description"],
                category=offer["category"],
                channel=channel,
                score=_finite(float(decision.score)),
                reason_codes=decision.reason_codes,
                policy_version=policy.policy_id,
            )

    # ── /showcase ────────────────────────────────────────────────
    async def showcase(self, cod_cliente: int, channel, top_k: int) -> ShowcaseResponse:
        async with self.uow:
            client = await self._require_client(cod_cliente)
            policy = await self._require_active_policy()
            states = [
                _orm_to_state(s)
                for s in await self.uow.estados_braco.list_by_policy(policy.policy_id)
            ]
            pol = build_policy(
                policy.algorithm, dimension=self.rt.stats.dimension, hyperparams=policy.hyperparams
            )

            ranked, _x, _ctx = self.rt.engine.rank(_client_to_dict(client), pol, states)
            items = [
                OfertaRankeada(
                    arm_id=r.arm_id,
                    product_name=self.rt.offers_by_id[r.arm_id]["product_name"],
                    description=self.rt.offers_by_id[r.arm_id]["description"],
                    category=self.rt.offers_by_id[r.arm_id]["category"],
                    score=_finite(float(r.score)),
                    reason_codes=r.reason_codes,
                    rank=i + 1,
                )
                for i, r in enumerate(ranked[:top_k])
            ]
            return ShowcaseResponse(
                cod_cliente=cod_cliente, policy_version=policy.policy_id, items=items
            )

    # ── /feedback ────────────────────────────────────────────────
    async def feedback(self, decision_id: UUID, event_type: TipoEvento) -> FeedbackResponse:
        async with self.uow:
            decision = await self._require_decision(decision_id)
            evt = EventoImpressao(decision_id=decision.decision_id, type=event_type)
            self.uow.eventos_impressao.add(evt)
            await self.uow.session.flush()
            return FeedbackResponse(
                event_id=evt.event_id,
                decision_id=decision.decision_id,
                type=event_type,
                occurred_at=evt.occurred_at or datetime.now(UTC),
            )

    # ── /reward ──────────────────────────────────────────────────
    async def reward(
        self, decision_id: UUID, converted: bool, value: float | None
    ) -> RewardResponse:
        async with self.uow:
            decision = await self._require_decision(decision_id)
            policy = await self.uow.politicas.get_by_policy_id(decision.policy_version)
            if policy is None:
                raise Conflict("Política da decisão não encontrada", code="POLICY_NOT_FOUND")

            # click = houve evento de clique OU o cliente converteu
            events = await self.uow.eventos_impressao.list_by_decision(decision_id)
            clicked = any(e.type == TipoEvento.CLICK for e in events) or converted
            reward_value = (
                float(value)
                if value is not None
                else self.rt.engine.reward_value(decision.chosen_arm_id, clicked)
            )

            # aprendizado: atualiza o estado do braço (LinUCB A/b, Thompson α/β, UCB n/sum)
            orm_state = await self.uow.estados_braco.get(policy.policy_id, decision.chosen_arm_id)
            if orm_state is None:
                orm_state = EstadoBraco(policy_id=policy.policy_id, arm_id=decision.chosen_arm_id)
                self.uow.estados_braco.add(orm_state)
            client = (
                await self.uow.clientes.get_by_cod_cliente(decision.cod_cliente)
                if decision.cod_cliente
                else None
            )
            if client is not None:
                state = self.rt.engine.decorate(_orm_to_state(orm_state))
                pol = build_policy(
                    policy.algorithm,
                    dimension=self.rt.stats.dimension,
                    hyperparams=policy.hyperparams,
                )
                x = self.rt.stats.context_vector(_client_to_dict(client))
                pol.update(state, reward_value, x)  # aplica exatamente a recompensa calculada
                self._write_state(orm_state, state)

            reward = await self.uow.recompensas.get_by_decision(decision_id)
            if reward is None:
                reward = Recompensa(decision_id=decision_id, value=reward_value)
                self.uow.recompensas.add(reward)
            reward.value = reward_value
            reward.status = StatusRecompensa.OBSERVED
            reward.observed_at = datetime.now(UTC)
            await self.uow.session.flush()
            return RewardResponse(
                reward_id=reward.reward_id,
                decision_id=decision_id,
                value=reward_value,
                status=reward.status,
            )

    # ── helpers ──────────────────────────────────────────────────
    @staticmethod
    def _write_state(orm: EstadoBraco, state: ArmState) -> None:
        orm.alpha, orm.beta = state.alpha, state.beta
        orm.n_pulls, orm.sum_reward = state.n_pulls, state.sum_reward
        orm.A, orm.b = state.A, state.b

    async def _require_client(self, cod_cliente: int):
        client = await self.uow.clientes.get_by_cod_cliente(cod_cliente)
        if client is None:
            raise NotFound("Cliente não encontrado", code="CLIENT_NOT_FOUND")
        return client

    async def _require_active_policy(self):
        policy = await self.uow.politicas.get_active()
        if policy is None:
            raise Conflict("Nenhuma política ativa", code="NO_ACTIVE_POLICY")
        return policy

    async def _require_decision(self, decision_id: UUID):
        decision = await self.uow.decisoes.get_by_decision_id(decision_id)
        if decision is None:
            raise NotFound("Decisão não encontrada", code="DECISION_NOT_FOUND")
        return decision
