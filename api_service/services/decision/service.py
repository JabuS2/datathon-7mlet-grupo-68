"""Serviço de serving: liga o model_service ao log auditável no Postgres.

Fluxo por endpoint:
  /decide      → ranqueia no model_service, persiste `Decisao` + `EventoImpressao(impression)`.
  /showcase    → ranqueia (somente leitura, sem persistir).
  /me/feedback → registra `EventoImpressao(click)`.
  /reward      → recompensa **binária** → `/update` no model_service + grava `Recompensa`.

O bandit não roda mais aqui. O que **fica** é a trilha auditável — `Decisao`,
`EventoImpressao` e `Recompensa` são chaveados por `cod_cliente` e vivem junto de
`clientes`, que é o que permite reconstruir por que uma oferta foi servida a quem.
`policy_version`, `reason_codes` e `context` vêm da resposta do `/rank`.
"""

from __future__ import annotations

import math
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from db.unit_of_work import UnitOfWork
from enums.decisao import StatusRecompensa, TipoEvento
from http_exceptions import Conflict, NotFound
from models.cliente import Cliente
from models.decisao import Decisao
from models.evento_impressao import EventoImpressao
from models.recompensa import Recompensa
from schemas.decisao import (
    DecideResponse,
    FeedbackResponse,
    OfertaRankeada,
    RewardResponse,
    ShowcaseResponse,
)
from services.model_client import ModelServiceClient
from settings import settings


def _finite(value: float) -> float:
    """Guarda contra inf/nan no JSON vindo de um score degenerado."""
    return value if math.isfinite(value) else 1e9


class DecisionService:
    def __init__(self, uow: UnitOfWork, model_client: ModelServiceClient | None = None):
        self.uow = uow
        self.model_client = model_client or ModelServiceClient()

    # ── /decide ──────────────────────────────────────────────────
    async def decide(self, cod_cliente: int, channel, arm_id: str | None = None) -> DecideResponse:
        """Registra uma decisão. Com `arm_id`, serve o braço escolhido na vitrine clicável."""
        async with self.uow:
            client = await self._require_client(cod_cliente)
            context, segments = client.to_context(), list(client.segmentos_sinteticos)
            known_arm = arm_id is None or await self.uow.ofertas.get_by_arm_id(arm_id) is not None

        if arm_id is not None and not known_arm:
            raise NotFound(f"Oferta desconhecida: {arm_id}", code="ARM_NOT_FOUND")

        result = await self.model_client.rank(settings.DEFAULT_ALGORITHM, context, segments)
        ranked = result["ranked"]
        if not ranked:
            raise Conflict("Nenhuma oferta elegível para o cliente", code="NO_ELIGIBLE_ARM")

        if arm_id is None:
            chosen, extra = ranked[0], []
        else:
            # `/rank` devolve só elegíveis; o braço existe (checado acima), então ausência
            # aqui significa inelegível — não id inválido.
            found = next((r for r in ranked if r["arm_id"] == arm_id), None)
            if found is None:
                raise Conflict(
                    f"Oferta {arm_id} não é elegível para este cliente", code="ARM_NOT_ELIGIBLE"
                )
            chosen, extra = found, ["user_selected"]

        audit = result.get("audit") or {}
        reasons = [
            *chosen.get("reason_codes", []),
            f"eligible:{len(audit.get('ofertas_elegiveis', []))}",
            *extra,
        ]

        async with self.uow:
            dec = Decisao(
                cod_cliente=cod_cliente,
                policy_version=result["policy_id"],
                chosen_arm_id=chosen["arm_id"],
                channel=channel,
                context=audit,
                reason_codes=reasons,
                score=_finite(float(chosen["score"])),
            )
            self.uow.decisoes.add(dec)
            await self.uow.session.flush()  # materializa decision_id (default uuid4)
            self.uow.eventos_impressao.add(
                EventoImpressao(decision_id=dec.decision_id, type=TipoEvento.IMPRESSION)
            )
            decision_id = dec.decision_id

        return DecideResponse(
            decision_id=decision_id,
            arm_id=chosen["arm_id"],
            product_name=chosen["product_name"],
            description=chosen["description"],
            category=chosen["category"],
            channel=channel,
            score=_finite(float(chosen["score"])),
            reason_codes=reasons,
            policy_version=result["policy_id"],
        )

    # ── /showcase ────────────────────────────────────────────────
    async def showcase(self, cod_cliente: int, channel, top_k: int) -> ShowcaseResponse:
        async with self.uow:
            client = await self._require_client(cod_cliente)
            context, segments = client.to_context(), list(client.segmentos_sinteticos)

        result = await self.model_client.rank(
            settings.DEFAULT_ALGORITHM, context, segments, top=top_k
        )
        items = [
            OfertaRankeada(
                arm_id=r["arm_id"],
                product_name=r["product_name"],
                description=r["description"],
                category=r["category"],
                score=_finite(float(r["score"])),
                reason_codes=r.get("reason_codes", []),
                rank=i + 1,
            )
            for i, r in enumerate(result["ranked"])
        ]
        return ShowcaseResponse(
            cod_cliente=cod_cliente, policy_version=result["policy_id"], items=items
        )

    # ── /me/feedback ─────────────────────────────────────────────
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
    async def reward(self, decision_id: UUID, converted: bool) -> RewardResponse:
        async with self.uow:
            decision = await self._require_decision(decision_id)
            events = await self.uow.eventos_impressao.list_by_decision(decision_id)
            # click = houve evento de clique OU o cliente converteu
            clicked = any(e.type == TipoEvento.CLICK for e in events) or converted
            reward_value = 1.0 if clicked else 0.0

            client = (
                await self.uow.clientes.get_by_cod_cliente(decision.cod_cliente)
                if decision.cod_cliente
                else None
            )
            context: dict[str, Any] = client.to_context() if client else {}
            segments = list(client.segmentos_sinteticos) if client else []
            arm_id, policy_version = decision.chosen_arm_id, decision.policy_version

        # aprendizado: aplica na política QUE GEROU a decisão, não na ativa de agora —
        # recompensa atrasada pode chegar depois de uma promoção.
        if client is not None:
            await self.model_client.update(
                settings.DEFAULT_ALGORITHM,
                arm_id,
                reward_value,
                context,
                segments,
                policy_id=policy_version,
            )

        async with self.uow:
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
    async def _require_client(self, cod_cliente: int) -> Cliente:
        client = await self.uow.clientes.get_by_cod_cliente(cod_cliente)
        if client is None:
            raise NotFound("Cliente não encontrado", code="CLIENT_NOT_FOUND")
        return client

    async def _require_decision(self, decision_id: UUID) -> Decisao:
        decision = await self.uow.decisoes.get_by_decision_id(decision_id)
        if decision is None:
            raise NotFound("Decisão não encontrada", code="DECISION_NOT_FOUND")
        return decision
