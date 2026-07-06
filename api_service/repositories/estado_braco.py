from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.estado_braco import EstadoBraco
from repositories.base import BaseRepository


class EstadoBracoRepository(BaseRepository[EstadoBraco]):
    """Pesos aprendidos por (política, braço). PK composta — getters específicos."""

    def __init__(self, session: AsyncSession):
        super().__init__(session, EstadoBraco)

    async def get(self, policy_id: str, arm_id: str) -> EstadoBraco | None:
        stmt = select(EstadoBraco).where(
            EstadoBraco.policy_id == policy_id, EstadoBraco.arm_id == arm_id
        )
        result: EstadoBraco | None = await self.session.scalar(stmt)
        return result

    async def list_by_policy(self, policy_id: str) -> list[EstadoBraco]:
        return await self.filter(EstadoBraco.policy_id == policy_id)
