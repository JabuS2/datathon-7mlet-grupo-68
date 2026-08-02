from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from models.evento_impressao import EventoImpressao
from repositories.base import BaseRepository


class EventoImpressaoRepository(BaseRepository[EventoImpressao]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, EventoImpressao)

    async def list_by_decision(self, decision_id: UUID) -> list[EventoImpressao]:
        return await self.filter(EventoImpressao.decision_id == decision_id)
