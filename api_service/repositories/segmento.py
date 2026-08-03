from sqlalchemy.ext.asyncio import AsyncSession

from models.segmento import Segmento
from repositories.base import BaseRepository


class SegmentoRepository(BaseRepository[Segmento]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, Segmento)

    async def get_by_segment_id(self, segment_id: str) -> Segmento | None:
        return await self.get_by_field(Segmento.segment_id, segment_id)
