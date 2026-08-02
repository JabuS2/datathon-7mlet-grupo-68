from sqlalchemy.ext.asyncio import AsyncSession

from enums.avaliacao import TipoCasoAvaliacao
from models.caso_avaliacao import CasoAvaliacao
from repositories.base import BaseRepository


class CasoAvaliacaoRepository(BaseRepository[CasoAvaliacao]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, CasoAvaliacao)

    async def list_by_type(self, tipo: TipoCasoAvaliacao) -> list[CasoAvaliacao]:
        return await self.filter(CasoAvaliacao.type == tipo)
