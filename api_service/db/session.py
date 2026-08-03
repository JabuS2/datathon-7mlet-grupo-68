from db.database import Database
from settings import settings


def get_database() -> Database:
    # Prefere DATABASE_URL (Docker/Compose) e cai para os POSTGRES_* — ver Settings.
    return Database(settings.async_database_url)


db = get_database()
