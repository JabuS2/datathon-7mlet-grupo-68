from datetime import datetime

from schemas.base import BaseSchema


class UserSummary(BaseSchema):
    email: str
    is_admin: bool
    created_at: datetime | None = None


class UsersOverview(BaseSchema):
    total_users: int
    admin_count: int
    signups_last_7_days: int
    signups_last_30_days: int
    latest_users: list[UserSummary]
