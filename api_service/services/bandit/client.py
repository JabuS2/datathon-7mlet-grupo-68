"""Facade local do bandit.

Mantém a superfície usada pelos serviços de negócio durante a consolidação, mas não faz
mais chamadas HTTP: ranking, atualização e governança rodam dentro do api_service.
"""

from __future__ import annotations

from typing import Any

from db.session import db
from services.bandit.dependencies import get_service
from services.bandit.governance import GovernanceService
from services.bandit.governance_schemas import MetricaPublish, RetrainCycleCreate
from services.bandit.governance_uow import UnitOfWork
from services.bandit.policy_resolver import resolve_policy


class BanditClient:
    async def rank(
        self,
        algorithm: str | None,
        client: dict[str, Any],
        segments: list[str],
        top: int | None = None,
        exclude_arm_ids: list[str] | None = None,
        policy_id: str | None = None,
    ) -> dict[str, Any]:
        async for session in db.session():
            async with UnitOfWork(session) as uow:
                service = get_service()
                policy = await resolve_policy(uow, policy_id, service._resolve_algorithm(algorithm))
                return await service.rank(algorithm, client, segments, top, exclude_arm_ids, policy)
        raise RuntimeError("database session was not created")

    async def update(
        self,
        algorithm: str | None,
        arm_id: str,
        reward: float,
        client: dict[str, Any],
        segments: list[str],
        policy_id: str | None = None,
    ) -> dict[str, Any]:
        async for session in db.session():
            async with UnitOfWork(session) as uow:
                service = get_service()
                policy = await resolve_policy(uow, policy_id, service._resolve_algorithm(algorithm))
                return await service.update(algorithm, arm_id, reward, client, segments, policy)
        raise RuntimeError("database session was not created")

    async def publish_metric(
        self, policy_id: str, metric: str, value: float, alert: bool = False
    ) -> dict[str, Any]:
        async for session in db.session():
            await GovernanceService(UnitOfWork(session)).publish_metric(
                MetricaPublish(policy_id=policy_id, metric=metric, value=value, alert=alert)
            )
            return {"policy_id": policy_id, "metric": metric, "value": value, "alert": alert}
        raise RuntimeError("database session was not created")

    async def start_retrain_cycle(
        self, policy_id: str, metrics: dict[str, Any], run_id: str | None = None
    ) -> dict[str, Any]:
        async for session in db.session():
            gov = GovernanceService(UnitOfWork(session))
            data = RetrainCycleCreate(policy_id=policy_id, metrics=metrics, run_id=run_id)
            response = await gov.start_cycle(data)
            return response.model_dump(mode="json")
        raise RuntimeError("database session was not created")
