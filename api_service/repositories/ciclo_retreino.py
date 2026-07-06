from sqlalchemy.ext.asyncio import AsyncSession

from enums.governanca import StatusCicloRetreino
from models.ciclo_retreino import CicloRetreino
from repositories.base import BaseRepository


class CicloRetreinoRepository(BaseRepository[CicloRetreino]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, CicloRetreino)

    async def get_by_run_id(self, run_id: str) -> CicloRetreino | None:
        return await self.get_by_field(CicloRetreino.run_id, run_id)

    async def list_by_status(self, status: StatusCicloRetreino) -> list[CicloRetreino]:
        return await self.filter(CicloRetreino.status == status)
