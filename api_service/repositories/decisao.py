from datetime import datetime
from uuid import UUID

from sqlalchemy import Float, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.decisao import Decisao
from models.recompensa import Recompensa
from repositories.base import BaseRepository


class DecisaoRepository(BaseRepository[Decisao]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, Decisao)

    async def get_by_decision_id(self, decision_id: UUID) -> Decisao | None:
        return await self.get_by_field(Decisao.decision_id, decision_id)

    async def list_by_cliente(self, cod_cliente: int) -> list[Decisao]:
        return await self.filter(Decisao.cod_cliente == cod_cliente)

    async def observations_since(
        self, since: datetime, policy_version: str | None = None
    ) -> list[tuple[str, float, float]]:
        """(arm_id, reward, renda_percentil) por decisão do período.

        LEFT JOIN em `recompensas`: decisão sem recompensa observada conta como reward 0 —
        não converter é informação, e descartá-la inflaria a taxa de conversão.
        """
        stmt = (
            select(
                Decisao.chosen_arm_id,
                func.coalesce(Recompensa.value, 0.0),
                Decisao.context["renda_percentil"].astext.cast(Float),
            )
            .outerjoin(Recompensa, Recompensa.decision_id == Decisao.decision_id)
            .where(Decisao.created_at >= since)
        )
        if policy_version:
            stmt = stmt.where(Decisao.policy_version == policy_version)
        result = await self.session.execute(stmt)
        return [(a, float(r or 0.0), float(p or 0.0)) for a, r, p in result.all()]

    async def renda_percentis_between(
        self, start: datetime, end: datetime, policy_version: str | None = None
    ) -> list[float]:
        """Percentis de renda das decisões da janela — entrada do PSI."""
        stmt = select(Decisao.context["renda_percentil"].astext.cast(Float)).where(
            Decisao.created_at >= start, Decisao.created_at < end
        )
        if policy_version:
            stmt = stmt.where(Decisao.policy_version == policy_version)
        result = await self.session.execute(stmt)
        return [float(v) for (v,) in result.all() if v is not None]

    async def policy_versions_since(self, since: datetime) -> list[str]:
        result = await self.session.execute(
            select(Decisao.policy_version)
            .where(Decisao.created_at >= since)
            .group_by(Decisao.policy_version)
        )
        return [v for (v,) in result.all()]
