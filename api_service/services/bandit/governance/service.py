"""Ciclo de vida de políticas com human-in-the-loop, agora no model_service.

Fluxo: registrar (`shadow`) → abrir ciclo de retreino (`candidate`) → approval gate humano
(`approve` promove / `reject` registra) → promoção atômica (uma `active` por vez) → rollback
auditável.

Migrado do api_service com uma diferença de fundo: **não existe `estados_braco`**. Os pesos
vivem no Redis chaveados por `policy_id`, então promover não copia estado e o rollback
recupera intacto — basta voltar a apontar `active` para a política anterior, cuja chave nunca
foi tocada. Antes, "preservar o conjunto de pesos de cada política" dependia de a tabela ter
sido escrita corretamente; agora é propriedade do jeito que o estado é chaveado.

Cálculo de métricas continua no api_service, que é quem tem `decisao`/`recompensa`. Aqui só
guardamos o valor publicado, para exibir ao lado da política que ele justificou.
"""

from __future__ import annotations

import logging
from uuid import uuid4

from db.governance_models import AprovacaoHumana, CicloRetreino, MetricaSnapshot, Politica
from enums.governanca import DecisaoAprovacao, StatusCicloRetreino
from enums.politica import StatusPolitica
from exceptions import AppException, NotFound
from services.bandit.governance_schemas import (
    AprovacaoCreate,
    AprovacaoResponse,
    CicloRetreinoResponse,
    MetricaPublish,
    MetricaResponse,
    PoliticaCreate,
    PoliticaResponse,
    RetrainCycleCreate,
)
from services.bandit.governance_uow import UnitOfWork
from services.bandit.policy_resolver import ResolvedPolicy

logger = logging.getLogger(__name__)


class Conflict(AppException):
    def __init__(self, message: str, code: str | None = None):
        super().__init__(message, 409, code)


class GovernanceService:
    def __init__(self, uow: UnitOfWork, snapshot=None):
        """`snapshot(policy) -> versão | None`: registra o estado da política no MLflow.

        Injetado em vez de importado para que abrir um ciclo continue funcionando (sem
        `registry_version`) quando o MLflow está fora — o gate humano não pode depender da
        disponibilidade do registry.
        """
        self.uow = uow
        self.snapshot = snapshot

    # ── políticas ────────────────────────────────────────────────
    async def register_policy(self, data: PoliticaCreate) -> PoliticaResponse:
        async with self.uow:
            if await self.uow.get_policy(data.policy_id):
                raise Conflict("Política já existe", code="POLICY_EXISTS")
            policy = Politica(
                policy_id=data.policy_id,
                version=data.version,
                algorithm=data.algorithm,
                hyperparams=data.hyperparams,
                status=StatusPolitica.SHADOW,
            )
            self.uow.add(policy)
            await self.uow.session.flush()
            return PoliticaResponse.model_validate(policy)

    async def list_policies(self) -> list[PoliticaResponse]:
        async with self.uow:
            return [PoliticaResponse.model_validate(p) for p in await self.uow.list_policies()]

    async def resolved(self, policy_id: str) -> ResolvedPolicy:
        """Política pronta para o `BanditService` (usada por `/policies/{id}/arms`)."""
        async with self.uow:
            policy = await self._require_policy(policy_id)
            return ResolvedPolicy(
                policy_id=policy.policy_id,
                algorithm=str(policy.algorithm),
                hyperparams=dict(policy.hyperparams or {}),
                governed=True,
            )

    async def promote_policy(self, policy_id: str) -> PoliticaResponse:
        async with self.uow:
            target = await self._require_policy(policy_id)
            await self._activate(target)
            await self.uow.session.flush()
            return PoliticaResponse.model_validate(target)

    # ── ciclo de retreino + approval gate ────────────────────────
    async def start_cycle(self, data: RetrainCycleCreate) -> CicloRetreinoResponse:
        """Abre um ciclo e **registra o snapshot do modelo no MLflow**.

        Antes o ciclo era só uma linha no banco: nada ligava a candidata ao artefato que ela
        representava, então aprovar era aprovar um `run_id` sem modelo anexo. Agora o estado
        da política é versionado no registry e o `registry_version` fica no ciclo — é o que
        permite recarregar exatamente aquele modelo num rollback.
        """
        async with self.uow:
            policy = await self._require_policy(data.policy_id)
            run_id = data.run_id or f"run-{uuid4().hex[:8]}"
            if await self.uow.get_cycle(run_id):
                raise Conflict("run_id já existe", code="RUN_EXISTS")
            resolved = ResolvedPolicy(
                policy_id=policy.policy_id,
                algorithm=str(policy.algorithm),
                hyperparams=dict(policy.hyperparams or {}),
                governed=True,
            )
            registry_version = await self._snapshot(resolved)
            cycle = CicloRetreino(
                run_id=run_id,
                policy_id=data.policy_id,
                status=StatusCicloRetreino.CANDIDATE,
                metrics=data.metrics,
                registry_version=registry_version,
            )
            self.uow.add(cycle)
            await self.uow.session.flush()
            return CicloRetreinoResponse.model_validate(cycle)

    async def list_cycles(self, policy_id: str | None = None) -> list[CicloRetreinoResponse]:
        async with self.uow:
            rows = await self.uow.list_cycles(policy_id)
            return [CicloRetreinoResponse.model_validate(c) for c in rows]

    async def decide_approval(self, data: AprovacaoCreate, user_id: int) -> AprovacaoResponse:
        async with self.uow:
            cycle = await self._require_cycle(data.run_id)
            gate = AprovacaoHumana(
                run_id=data.run_id, user_id=user_id, decision=data.decision, note=data.note
            )
            self.uow.add(gate)

            if data.decision == DecisaoAprovacao.APPROVE:
                candidate = await self._require_policy(cycle.policy_id)
                await self._activate(candidate)
                cycle.status = StatusCicloRetreino.PROMOTED
            else:
                cycle.status = StatusCicloRetreino.REJECTED

            await self.uow.session.flush()
            return AprovacaoResponse.model_validate(gate)

    async def rollback(self, run_id: str, to_policy_id: str) -> CicloRetreinoResponse:
        async with self.uow:
            cycle = await self._require_cycle(run_id)
            promoted = await self.uow.get_policy(cycle.policy_id)
            if promoted:
                promoted.status = StatusPolitica.RETIRED
            target = await self._require_policy(to_policy_id)
            await self._activate(target)
            cycle.status = StatusCicloRetreino.ROLLED_BACK
            await self.uow.session.flush()
            return CicloRetreinoResponse.model_validate(cycle)

    # ── métricas (calculadas no api_service) ─────────────────────
    async def publish_metric(self, data: MetricaPublish) -> MetricaResponse:
        async with self.uow:
            await self._require_policy(data.policy_id)
            metric = MetricaSnapshot(
                policy_id=data.policy_id, metric=data.metric, value=data.value, alert=data.alert
            )
            self.uow.add(metric)
            await self.uow.session.flush()
            return MetricaResponse.model_validate(metric)

    async def list_metrics(
        self, policy_id: str | None = None, alerts_only: bool = False
    ) -> list[MetricaResponse]:
        async with self.uow:
            rows = await self.uow.list_metrics(policy_id, alerts_only)
            return [MetricaResponse.model_validate(r) for r in rows]

    # ── helpers ──────────────────────────────────────────────────
    async def _snapshot(self, policy: ResolvedPolicy) -> str | None:
        """Versiona o estado da política. Falha do registry **não** aborta o ciclo."""
        if self.snapshot is None:
            return None
        try:
            return await self.snapshot(policy)
        except Exception:
            logger.exception("registry_snapshot_failed", extra={"policy_id": policy.policy_id})
            return None

    async def _activate(self, policy: Politica) -> None:
        """Torna `policy` a única ativa; aposenta as demais.

        Não move pesos: a chave Redis de cada política é independente, então a anterior
        continua intacta e disponível para rollback.
        """
        for active in await self.uow.list_active_policies():
            if active.policy_id != policy.policy_id:
                active.status = StatusPolitica.RETIRED
        policy.status = StatusPolitica.ACTIVE

    async def _require_policy(self, policy_id: str) -> Politica:
        policy = await self.uow.get_policy(policy_id)
        if policy is None:
            raise NotFound("Política não encontrada", code="POLICY_NOT_FOUND")
        return policy

    async def _require_cycle(self, run_id: str) -> CicloRetreino:
        cycle = await self.uow.get_cycle(run_id)
        if cycle is None:
            raise NotFound("Ciclo de retreino não encontrado", code="CYCLE_NOT_FOUND")
        return cycle
