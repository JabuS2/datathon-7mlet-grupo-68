from models.politica import Politica
from repositories.base import BaseRepository
from sqlalchemy.ext.asyncio import AsyncSession

from enums.politica import StatusPolitica


class PoliticaRepository(BaseRepository[Politica]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, Politica)

    async def get_by_policy_id(self, policy_id: str) -> Politica | None:
        return await self.get_by_field(Politica.policy_id, policy_id)

    async def get_active(self) -> Politica | None:
        """A política que atende `/decide` (status='active'). Assume no máximo uma ativa."""
        return await self.get_by_field(Politica.status, StatusPolitica.ACTIVE)

    async def list_by_status(self, status: StatusPolitica) -> list[Politica]:
        return await self.filter(Politica.status == status)
