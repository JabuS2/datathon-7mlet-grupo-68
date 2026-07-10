from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.user import User
from repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, User)

    async def get_by_email(self, email: str) -> User | None:
        return await self.get_by_field(User.email, email)

    async def count_all(self) -> int:
        result = await self.session.scalar(select(func.count()).select_from(User))
        return int(result or 0)

    async def count_admins(self) -> int:
        result = await self.session.scalar(
            select(func.count()).select_from(User).where(User.is_admin.is_(True))
        )
        return int(result or 0)

    async def count_created_since(self, since: datetime) -> int:
        result = await self.session.scalar(
            select(func.count()).select_from(User).where(User.created_at >= since)
        )
        return int(result or 0)

    async def latest(self, limit: int = 5) -> list[User]:
        result = await self.session.execute(
            select(User).order_by(User.created_at.desc()).limit(limit)
        )
        return list(result.scalars().all())
