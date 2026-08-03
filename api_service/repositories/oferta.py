from sqlalchemy.ext.asyncio import AsyncSession

from enums.catalogo import CategoriaOferta
from models.oferta import Oferta
from repositories.base import BaseRepository


class OfertaRepository(BaseRepository[Oferta]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, Oferta)

    async def get_by_arm_id(self, arm_id: str) -> Oferta | None:
        return await self.get_by_field(Oferta.arm_id, arm_id)

    async def list_by_category(self, category: CategoriaOferta) -> list[Oferta]:
        return await self.filter(Oferta.category == category)
