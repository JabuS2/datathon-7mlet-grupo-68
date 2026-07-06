from sqlalchemy.ext.asyncio import AsyncSession

from models.metrica_monitoramento import MetricaMonitoramento
from repositories.base import BaseRepository


class MetricaMonitoramentoRepository(BaseRepository[MetricaMonitoramento]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, MetricaMonitoramento)

    async def list_by_policy(self, policy_id: str) -> list[MetricaMonitoramento]:
        return await self.filter(MetricaMonitoramento.policy_id == policy_id)

    async def list_alerts(self) -> list[MetricaMonitoramento]:
        return await self.filter(MetricaMonitoramento.alert.is_(True))
