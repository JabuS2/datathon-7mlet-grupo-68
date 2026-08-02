from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from enums.decisao import StatusRecompensa
from models.recompensa import Recompensa
from repositories.base import BaseRepository


class RecompensaRepository(BaseRepository[Recompensa]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, Recompensa)

    async def get_by_decision(self, decision_id: UUID) -> Recompensa | None:
        return await self.get_by_field(Recompensa.decision_id, decision_id)

    async def list_pending(self) -> list[Recompensa]:
        """Recompensas atrasadas ainda não observadas (delayed rewards)."""
        return await self.filter(Recompensa.status == StatusRecompensa.PENDING)
