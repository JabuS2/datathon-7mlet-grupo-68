from sqlalchemy.ext.asyncio import AsyncSession

from repositories.user import UserRepository


class UnitOfWork:
    def __init__(self, session: AsyncSession):
        self.session = session
        self._users: UserRepository | None = None

    @property
    def users(self) -> UserRepository:
        if self._users is None:
            self._users = UserRepository(self.session)
        return self._users

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        try:
            if exc_type:
                await self.session.rollback()
            else:
                await self.session.flush()
                await self.session.commit()
        finally:
            pass