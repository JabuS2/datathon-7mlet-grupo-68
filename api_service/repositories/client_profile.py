from sqlalchemy.ext.asyncio import AsyncSession

from models.client_profile import ClientProfile
from repositories.base import BaseRepository


class ClientProfileRepository(BaseRepository[ClientProfile]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, ClientProfile)

    async def get_by_user_id(self, user_id: int) -> ClientProfile | None:
        return await self.get_by_field(ClientProfile.user_id, user_id)
