from sqlalchemy.ext.asyncio import AsyncSession

from models.feedback import FeedbackEvent
from repositories.base import BaseRepository


class FeedbackRepository(BaseRepository[FeedbackEvent]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, FeedbackEvent)

    async def get_by_user_id(self, user_id: int) -> list[FeedbackEvent]:
        return await self.filter(FeedbackEvent.user_id == user_id)
