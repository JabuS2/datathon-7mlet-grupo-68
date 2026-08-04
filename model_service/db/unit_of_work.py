from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import AprovacaoHumana, CicloRetreino, MetricaSnapshot, Politica
from enums import StatusPolitica


class UnitOfWork:
    """Transação + acesso às tabelas de governança.

    Pequeno o bastante para dispensar a camada de repositórios do api_service: são três
    agregados e um punhado de consultas.
    """

    def __init__(self, session: AsyncSession):
        self.session = session

    async def __aenter__(self) -> UnitOfWork:
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        try:
            if exc_type:
                await self.session.rollback()
            else:
                try:
                    await self.session.commit()
                except Exception:
                    await self.session.rollback()
                    raise
        finally:
            await self.session.close()

    def add(self, entity: object) -> None:
        self.session.add(entity)

    # ── políticas ────────────────────────────────────────────────
    async def get_policy(self, policy_id: str) -> Politica | None:
        return await self.session.get(Politica, policy_id)

    async def list_policies(self) -> list[Politica]:
        result = await self.session.execute(select(Politica).order_by(Politica.policy_id))
        return list(result.scalars().all())

    async def get_active_policy(self) -> Politica | None:
        return await self.session.scalar(
            select(Politica).where(Politica.status == StatusPolitica.ACTIVE).limit(1)
        )

    async def list_active_policies(self) -> list[Politica]:
        result = await self.session.execute(
            select(Politica).where(Politica.status == StatusPolitica.ACTIVE)
        )
        return list(result.scalars().all())

    # ── ciclos de retreino ───────────────────────────────────────
    async def get_cycle(self, run_id: str) -> CicloRetreino | None:
        return await self.session.get(CicloRetreino, run_id)

    async def list_cycles(self, policy_id: str | None = None) -> list[CicloRetreino]:
        stmt = select(CicloRetreino).order_by(CicloRetreino.created_at.desc())
        if policy_id:
            stmt = stmt.where(CicloRetreino.policy_id == policy_id)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    # ── aprovações ───────────────────────────────────────────────
    async def list_approvals(self, run_id: str) -> list[AprovacaoHumana]:
        result = await self.session.execute(
            select(AprovacaoHumana).where(AprovacaoHumana.run_id == run_id)
        )
        return list(result.scalars().all())

    # ── métricas publicadas pelo api_service ─────────────────────
    async def list_metrics(
        self, policy_id: str | None = None, alerts_only: bool = False
    ) -> list[MetricaSnapshot]:
        stmt = select(MetricaSnapshot).order_by(MetricaSnapshot.created_at.desc())
        if policy_id:
            stmt = stmt.where(MetricaSnapshot.policy_id == policy_id)
        if alerts_only:
            stmt = stmt.where(MetricaSnapshot.alert.is_(True))
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
