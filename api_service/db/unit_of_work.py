from sqlalchemy.ext.asyncio import AsyncSession

from repositories.client_profile import ClientProfileRepository
from repositories.feedback import FeedbackRepository
from repositories.user import UserRepository


class UnitOfWork:
    def __init__(self, session: AsyncSession):
        self.session = session
        self._users: UserRepository | None = None
        self._profiles: ClientProfileRepository | None = None
        self._feedback: FeedbackRepository | None = None

    @property
    def users(self):
        if self._users is None:
            self._users = UserRepository(self.session)
        return self._users

    @property
    def profiles(self):
        if self._profiles is None:
            self._profiles = ClientProfileRepository(self.session)
        return self._profiles

    @property
    def feedback(self):
        if self._feedback is None:
            self._feedback = FeedbackRepository(self.session)
        return self._feedback

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        try:
            if exc_type:
                await self.session.rollback()
            else:
                try:
                    await self.session.commit()
                except Exception:
                    await self.session.rollback()
                    raise
        finally:
            await self.session.close()
