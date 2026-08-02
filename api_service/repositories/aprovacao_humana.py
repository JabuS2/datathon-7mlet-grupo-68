from sqlalchemy.ext.asyncio import AsyncSession

from models.aprovacao_humana import AprovacaoHumana
from repositories.base import BaseRepository


class AprovacaoHumanaRepository(BaseRepository[AprovacaoHumana]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, AprovacaoHumana)

    async def list_by_run(self, run_id: str) -> list[AprovacaoHumana]:
        return await self.filter(AprovacaoHumana.run_id == run_id)
