"""Governança & MLOps (Etapa 7): ciclo de vida de políticas com human-in-the-loop.

Fluxo: registrar política (`shadow`) → abrir ciclo de retreino (`candidate`) → approval gate humano
(`approve`→promove / `reject`→registra) → promoção controlada (uma ativa por vez) → rollback
auditável. Mais monitoramento (regret/conversão/reward/PSI drift) com flag de alerta.

Promoção é atômica: no máximo UMA política `active` por vez; promover uma aposenta a anterior,
preservando o conjunto de pesos de cada política em `estado_braco` (rollback recupera intacto).
"""

from __future__ import annotations

from uuid import uuid4

from db.unit_of_work import UnitOfWork
from enums.governanca import DecisaoAprovacao, StatusCicloRetreino
from enums.politica import StatusPolitica
from http_exceptions import Conflict, NotFound
from models.aprovacao_humana import AprovacaoHumana
from models.ciclo_retreino import CicloRetreino
from models.estado_braco import EstadoBraco
from models.metrica_monitoramento import MetricaMonitoramento
from models.politica import Politica
from schemas.governanca import (
    AprovacaoHumanaCreate,
    AprovacaoHumanaResponse,
    CicloRetreinoResponse,
    MetricaCreate,
    MetricaResponse,
    RetrainCycleCreate,
)
from schemas.politica import EstadoBracoResponse, PoliticaCreate, PoliticaResponse


class GovernanceService:
    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    # ── políticas ────────────────────────────────────────────────
    async def register_policy(self, data: PoliticaCreate) -> PoliticaResponse:
        async with self.uow:
            if await self.uow.politicas.get_by_policy_id(data.policy_id):
                raise Conflict("Política já existe", code="POLICY_EXISTS")
            policy = Politica(
                policy_id=data.policy_id, version=data.version, algorithm=data.algorithm,
                hyperparams=data.hyperparams, status=StatusPolitica.SHADOW,
            )
            self.uow.politicas.add(policy)
            await self._seed_arm_states(policy.policy_id)
            await self.uow.session.flush()
            return PoliticaResponse.model_validate(policy)

    async def list_policies(self) -> list[PoliticaResponse]:
        async with self.uow:
            return [PoliticaResponse.model_validate(p) for p in await self.uow.politicas.get_all()]

    async def list_arm_states(self, policy_id: str) -> list[EstadoBracoResponse]:
        async with self.uow:
            await self._require_policy(policy_id)
            states = await self.uow.estados_braco.list_by_policy(policy_id)
            return [EstadoBracoResponse.model_validate(s) for s in states]

    async def promote_policy(self, policy_id: str) -> PoliticaResponse:
        async with self.uow:
            target = await self._require_policy(policy_id)
            await self._activate(target)
            await self.uow.session.flush()
            return PoliticaResponse.model_validate(target)

    # ── ciclo de retreino + approval gate ────────────────────────
    async def start_cycle(self, data: RetrainCycleCreate) -> CicloRetreinoResponse:
        async with self.uow:
            await self._require_policy(data.policy_id)
            run_id = data.run_id or f"run-{uuid4().hex[:8]}"
            if await self.uow.ciclos_retreino.get_by_run_id(run_id):
                raise Conflict("run_id já existe", code="RUN_EXISTS")
            cycle = CicloRetreino(
                run_id=run_id, policy_id=data.policy_id,
                status=StatusCicloRetreino.CANDIDATE, metrics=data.metrics,
            )
            self.uow.ciclos_retreino.add(cycle)
            await self.uow.session.flush()
            return CicloRetreinoResponse.model_validate(cycle)

    async def decide_approval(
        self, data: AprovacaoHumanaCreate, user_id: int
    ) -> AprovacaoHumanaResponse:
        async with self.uow:
            cycle = await self._require_cycle(data.run_id)
            gate = AprovacaoHumana(
                run_id=data.run_id, user_id=user_id, decision=data.decision, note=data.note
            )
            self.uow.aprovacoes_humanas.add(gate)

            if data.decision == DecisaoAprovacao.APPROVE:
                # promove a política candidata para produção controlada
                candidate = await self._require_policy(cycle.policy_id)
                await self._activate(candidate)
                cycle.status = StatusCicloRetreino.PROMOTED
            else:
                cycle.status = StatusCicloRetreino.APPROVED  # avaliado, mas não promovido

            await self.uow.session.flush()
            return AprovacaoHumanaResponse.model_validate(gate)

    async def rollback(self, run_id: str, to_policy_id: str) -> CicloRetreinoResponse:
        async with self.uow:
            cycle = await self._require_cycle(run_id)
            promoted = await self.uow.politicas.get_by_policy_id(cycle.policy_id)
            if promoted:
                promoted.status = StatusPolitica.RETIRED
            target = await self._require_policy(to_policy_id)
            await self._activate(target)
            cycle.status = StatusCicloRetreino.ROLLED_BACK
            await self.uow.session.flush()
            return CicloRetreinoResponse.model_validate(cycle)

    # ── monitoramento ────────────────────────────────────────────
    async def record_metric(self, data: MetricaCreate) -> MetricaResponse:
        async with self.uow:
            await self._require_policy(data.policy_id)
            metric = MetricaMonitoramento(
                policy_id=data.policy_id, metric=data.metric, value=data.value, alert=data.alert
            )
            self.uow.metricas_monitoramento.add(metric)
            await self.uow.session.flush()
            return MetricaResponse.model_validate(metric)

    async def list_metrics(
        self, policy_id: str | None = None, alerts_only: bool = False
    ) -> list[MetricaResponse]:
        async with self.uow:
            if alerts_only:
                rows = await self.uow.metricas_monitoramento.list_alerts()
            elif policy_id:
                rows = await self.uow.metricas_monitoramento.list_by_policy(policy_id)
            else:
                rows = await self.uow.metricas_monitoramento.get_all()
            return [MetricaResponse.model_validate(r) for r in rows]

    # ── helpers ──────────────────────────────────────────────────
    async def _activate(self, policy: Politica) -> None:
        """Torna `policy` a única ativa; aposenta as demais ativas."""
        for active in await self.uow.politicas.list_by_status(StatusPolitica.ACTIVE):
            if active.policy_id != policy.policy_id:
                active.status = StatusPolitica.RETIRED
        policy.status = StatusPolitica.ACTIVE

    async def _seed_arm_states(self, policy_id: str) -> None:
        for offer in await self.uow.ofertas.get_all():
            if await self.uow.estados_braco.get(policy_id, offer.arm_id) is None:
                self.uow.estados_braco.add(EstadoBraco(policy_id=policy_id, arm_id=offer.arm_id))

    async def _require_policy(self, policy_id: str) -> Politica:
        policy = await self.uow.politicas.get_by_policy_id(policy_id)
        if policy is None:
            raise NotFound("Política não encontrada", code="POLICY_NOT_FOUND")
        return policy

    async def _require_cycle(self, run_id: str) -> CicloRetreino:
        cycle = await self.uow.ciclos_retreino.get_by_run_id(run_id)
        if cycle is None:
            raise NotFound("Ciclo de retreino não encontrado", code="CYCLE_NOT_FOUND")
        return cycle
