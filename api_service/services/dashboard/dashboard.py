from datetime import UTC, datetime, timedelta

from db.unit_of_work import UnitOfWork
from schemas.dashboard import UsersOverview, UserSummary


class DashboardService:
    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    async def users_overview(self, latest_limit: int = 5) -> UsersOverview:
        async with self.uow:
            now = datetime.now(UTC).replace(tzinfo=None)

            total_users = await self.uow.users.count_all()
            admin_count = await self.uow.users.count_admins()
            signups_last_7_days = await self.uow.users.count_created_since(now - timedelta(days=7))
            signups_last_30_days = await self.uow.users.count_created_since(
                now - timedelta(days=30)
            )
            latest = await self.uow.users.latest(latest_limit)

            return UsersOverview(
                total_users=total_users,
                admin_count=admin_count,
                signups_last_7_days=signups_last_7_days,
                signups_last_30_days=signups_last_30_days,
                latest_users=[UserSummary.model_validate(user) for user in latest],
            )
