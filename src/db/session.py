from src.db.database import Database
from src.settings import settings


def get_database() -> Database:
    database_url = (
        f"postgresql+asyncpg://"
        f"{settings.POSTGRES_USER}:"
        f"{settings.POSTGRES_PASSWORD}@"
        f"{settings.POSTGRES_SERVER}:"
        f"{settings.POSTGRES_PORT}/"
        f"{settings.POSTGRES_DB}"
    )

    return Database(database_url)


db = get_database()