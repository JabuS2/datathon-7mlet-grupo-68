from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from models.decisao import Decisao
from repositories.base import BaseRepository


class DecisaoRepository(BaseRepository[Decisao]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, Decisao)

    async def get_by_decision_id(self, decision_id: UUID) -> Decisao | None:
        return await self.get_by_field(Decisao.decision_id, decision_id)

    async def list_by_cliente(self, cod_cliente: int) -> list[Decisao]:
        return await self.filter(Decisao.cod_cliente == cod_cliente)
