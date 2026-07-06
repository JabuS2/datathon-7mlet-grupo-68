from sqlalchemy.ext.asyncio import AsyncSession

from models.regra_adequacao import RegraAdequacao
from repositories.base import BaseRepository


class RegraAdequacaoRepository(BaseRepository[RegraAdequacao]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, RegraAdequacao)

    async def list_by_arm(self, arm_id: str) -> list[RegraAdequacao]:
        return await self.filter(RegraAdequacao.arm_id == arm_id)
