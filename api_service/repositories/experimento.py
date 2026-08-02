from sqlalchemy.ext.asyncio import AsyncSession

from models.experimento import Experimento
from repositories.base import BaseRepository


class ExperimentoRepository(BaseRepository[Experimento]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, Experimento)

    async def get_by_experiment_id(self, experiment_id: str) -> Experimento | None:
        return await self.get_by_field(Experimento.experiment_id, experiment_id)
