"""Monitoramento: calcula as métricas do log auditável e publica no model_service.

Por que o cálculo mora aqui e não lá: regret, conversão e PSI derivam de `decisao` e
`recompensa`, que ficaram no api_service junto de `clientes`. O model_service não tem esses
dados — ele recebe o número pronto em `POST /metrics` e o exibe ao lado da política que o
número justificou.

Antes disso não havia cálculo nenhum: `POST /metrics` do api_service gravava o valor que o
chamador mandasse, o que fazia do "monitoramento com alerta de drift" uma tabela preenchida
à mão.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta
from typing import Protocol

from services.bandit.client import BanditClient
from services.monitoring.metrics import Metric, build_metrics

logger = logging.getLogger(__name__)

#: Janela padrão de apuração. A metade mais antiga vira referência do PSI e a mais recente,
#: o período corrente — assim o drift é medido contra o próprio histórico, sem depender de
#: um snapshot externo que alguém teria de manter.
DEFAULT_WINDOW_DAYS = 14


class MonitoringRepository(Protocol):
    async def observations_since(
        self, start: datetime, policy_version: str | None
    ) -> list[tuple[str, float, float]]: ...
    async def renda_percentis_between(
        self, start: datetime, end: datetime, policy_version: str | None
    ) -> list[float]: ...
    async def policy_versions_since(self, since: datetime) -> list[str]: ...


class MonitoringUnitOfWork(Protocol):
    @property
    def decisoes(self) -> MonitoringRepository: ...

    async def __aenter__(self) -> MonitoringUnitOfWork: ...
    async def __aexit__(self, exc_type: object, exc: object, tb: object) -> None: ...


class MetricPublisher(Protocol):
    async def publish_metric(
        self, *, policy_id: str, metric: str, value: float, alert: bool
    ) -> dict[str, object]: ...


def _utc_naive() -> datetime:
    """Agora em UTC, **sem** tzinfo.

    `Base.created_at` é `TIMESTAMP WITHOUT TIME ZONE`; comparar com um datetime aware faz o
    asyncpg recusar o parâmetro ("can't subtract offset-naive and offset-aware datetimes").
    """
    return datetime.now(UTC).replace(tzinfo=None)


class MonitoringService:
    def __init__(
        self,
        uow: MonitoringUnitOfWork,
        model_client: MetricPublisher | None = None,
    ):
        self.uow = uow
        self.model_client = model_client or BanditClient()

    async def compute(
        self, policy_version: str | None = None, window_days: int = DEFAULT_WINDOW_DAYS
    ) -> dict[str, list[Metric] | str | int]:
        now = _utc_naive()
        start = now - timedelta(days=window_days)
        middle = now - timedelta(days=window_days / 2)

        async with self.uow:
            rows = await self.uow.decisoes.observations_since(start, policy_version)
            reference = await self.uow.decisoes.renda_percentis_between(
                start, middle, policy_version
            )
            current = await self.uow.decisoes.renda_percentis_between(middle, now, policy_version)

        observations = [(arm, reward) for arm, reward, _ in rows]
        metrics = build_metrics(observations, reference, current)

        logger.info(
            "metrics_computed",
            extra={
                "policy_version": policy_version,
                "window_days": window_days,
                "decisions": len(observations),
                **{m.name: m.value for m in metrics},
            },
        )
        return {
            "policy_version": policy_version or "",
            "window_days": window_days,
            "decisions": len(observations),
            "metrics": metrics,
        }

    async def publish(
        self, policy_version: str, window_days: int = DEFAULT_WINDOW_DAYS
    ) -> dict[str, list[Metric] | str | int]:
        """Calcula e publica no model_service, para exibição junto da política."""
        result = await self.compute(policy_version, window_days)
        metrics: list[Metric] = result["metrics"]  # type: ignore[assignment]
        for metric in metrics:
            await self.model_client.publish_metric(
                policy_id=policy_version,
                metric=metric.name,
                value=metric.value,
                alert=metric.alert,
            )
        logger.info(
            "metrics_published",
            extra={"policy_version": policy_version, "count": len(metrics)},
        )
        return result

    async def active_policy_versions(self, window_days: int = DEFAULT_WINDOW_DAYS) -> list[str]:
        """Políticas que produziram decisões no período — o que vale a pena apurar."""
        since = _utc_naive() - timedelta(days=window_days)
        async with self.uow:
            return await self.uow.decisoes.policy_versions_since(since)
