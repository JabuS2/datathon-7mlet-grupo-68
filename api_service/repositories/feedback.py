from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.feedback import FeedbackEvent
from repositories.base import BaseRepository


class FeedbackRepository(BaseRepository[FeedbackEvent]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, FeedbackEvent)

    async def get_by_user_id(self, user_id: int) -> list[FeedbackEvent]:
        return await self.filter(FeedbackEvent.user_id == user_id)

    async def clicked_arms(self, user_id: int) -> list[tuple[str, int, datetime]]:
        """(arm_id, nº de cliques, último clique) das ofertas em que o usuário demonstrou
        interesse — a "carteira".

        Agrupado por braço: clicar duas vezes na mesma oferta é mais interesse, não dois
        itens na carteira. Ordenado pelo clique mais recente.
        """
        stmt = (
            select(
                FeedbackEvent.arm_id,
                func.count().label("cliques"),
                func.max(FeedbackEvent.created_at).label("ultimo"),
            )
            .where(FeedbackEvent.user_id == user_id, FeedbackEvent.clicked.is_(True))
            .group_by(FeedbackEvent.arm_id)
            .order_by(func.max(FeedbackEvent.created_at).desc())
        )
        result = await self.session.execute(stmt)
        return [(arm, int(n), ultimo) for arm, n, ultimo in result.all()]
