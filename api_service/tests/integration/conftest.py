from __future__ import annotations

import os
from collections.abc import AsyncGenerator, Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path

import httpx
import jwt
import pytest
import pytest_asyncio
from fastapi import Depends, FastAPI
from sqlalchemy import text
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import NullPool
from testcontainers.postgres import PostgresContainer

from alembic import command
from alembic.config import Config
from core.jwt_token import JwtToken
from db.dependencies import get_db, get_uow
from db.unit_of_work import UnitOfWork
from main import app as fastapi_app

PROJECT_ROOT = Path(__file__).resolve().parents[2]

TEST_DATABASE_USER = "test"
TEST_DATABASE_PASSWORD = "test"
TEST_DATABASE_NAME = "api_service_test"
POSTGRES_IMAGE = "postgres:15-alpine"

USE_TESTCONTAINERS = os.getenv("USE_TESTCONTAINERS", "true").lower() == "true"


@dataclass(frozen=True)
class TestDatabase:
    sync_url: str
    async_url: str


def _assert_test_database_url(database_url: str) -> None:
    url = make_url(database_url)

    if url.get_backend_name() != "postgresql":
        raise RuntimeError("Integration tests require PostgreSQL.")

    if url.database != TEST_DATABASE_NAME:
        raise RuntimeError("Refusing to run tests outside isolated test database.")


@contextmanager
def _patched_database_env(database_url: str) -> Iterator[None]:
    url = make_url(database_url)
    _assert_test_database_url(database_url)

    values = {
        "POSTGRES_USER": url.username or "",
        "POSTGRES_PASSWORD": url.password or "",
        "POSTGRES_SERVER": url.host or "",
        "POSTGRES_PORT": str(url.port or 5432),
        "POSTGRES_DB": url.database or "",
    }

    previous = {k: os.environ.get(k) for k in values}
    os.environ.update(values)

    try:
        yield
    finally:
        for k, v in previous.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v


def _alembic_config(database_url: str) -> Config:
    config = Config(str(PROJECT_ROOT / "alembic.ini"))
    config.set_main_option("script_location", str(PROJECT_ROOT / "alembic"))
    config.set_main_option("sqlalchemy.url", database_url)
    return config


async def _truncate_public_tables(engine: AsyncEngine) -> None:
    query = text(
        """
        SELECT schemaname, tablename
        FROM pg_tables
        WHERE schemaname = 'public'
          AND tablename != 'alembic_version'
    """
    )

    async with engine.begin() as conn:
        result = await conn.execute(query)
        tables = result.all()

        if not tables:
            return

        preparer = engine.sync_engine.dialect.identifier_preparer

        table_names = ", ".join(
            f"{preparer.quote_schema(s)}.{preparer.quote(t)}" for s, t in tables
        )

        await conn.execute(text(f"TRUNCATE TABLE {table_names} RESTART IDENTITY CASCADE"))


@pytest.fixture(scope="session")
def postgres_container() -> Iterator[PostgresContainer | None]:
    if not USE_TESTCONTAINERS:
        yield None
        return

    with PostgresContainer(
        POSTGRES_IMAGE,
        username=TEST_DATABASE_USER,
        password=TEST_DATABASE_PASSWORD,
        dbname=TEST_DATABASE_NAME,
        driver="psycopg2",
    ) as postgres:
        yield postgres


@pytest.fixture(scope="session", autouse=True)
def migrated_postgres(postgres_container) -> Iterator[TestDatabase]:
    if USE_TESTCONTAINERS:
        sync_url = postgres_container.get_connection_url(driver=None)
        async_url = postgres_container.get_connection_url(driver="asyncpg")
    else:
        sync_url = os.environ["DATABASE_URL"]
        async_url = sync_url.replace("postgresql://", "postgresql+asyncpg://")

    _assert_test_database_url(sync_url)

    with _patched_database_env(sync_url):
        command.upgrade(_alembic_config(sync_url), "head")
        yield TestDatabase(sync_url=sync_url, async_url=async_url)


@pytest_asyncio.fixture
async def async_engine(migrated_postgres: TestDatabase) -> AsyncGenerator[AsyncEngine, None]:
    engine = create_async_engine(
        migrated_postgres.async_url,
        echo=False,
        poolclass=NullPool,
    )

    try:
        yield engine
    finally:
        await engine.dispose()


@pytest_asyncio.fixture(autouse=True)
async def clean_database(async_engine: AsyncEngine) -> AsyncGenerator[None, None]:
    await _truncate_public_tables(async_engine)
    try:
        yield
    finally:
        await _truncate_public_tables(async_engine)


@pytest.fixture
def session_factory(async_engine: AsyncEngine):
    return async_sessionmaker(
        bind=async_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )


@pytest_asyncio.fixture
async def db_session(session_factory):
    async with session_factory() as session:
        try:
            yield session
        finally:
            await session.rollback()


@pytest_asyncio.fixture
async def uow(db_session):
    async with UnitOfWork(db_session) as uow:
        yield uow


@pytest.fixture
def app(session_factory: async_sessionmaker[AsyncSession]) -> Iterator[FastAPI]:
    async def override_get_db():
        async with session_factory() as session:
            yield session

    async def override_get_uow(session: AsyncSession = Depends(override_get_db)):
        async with UnitOfWork(session) as uow:
            yield uow

    fastapi_app.dependency_overrides[get_db] = override_get_db
    fastapi_app.dependency_overrides[get_uow] = override_get_uow

    try:
        yield fastapi_app
    finally:
        fastapi_app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def async_client(app: FastAPI):
    transport = httpx.ASGITransport(app=app)

    async with httpx.AsyncClient(
        transport=transport,
        base_url="http://testserver/api/v1",
    ) as client:
        yield client


@pytest_asyncio.fixture
async def client(async_client):
    yield async_client


@pytest_asyncio.fixture
async def expired_token() -> str:
    jwt_token = JwtToken()

    payload = {
        "sub": "1",
        "iat": int((datetime.now(UTC) - timedelta(hours=2)).timestamp()),
        "exp": int((datetime.now(UTC) - timedelta(hours=1)).timestamp()),
    }

    return jwt.encode(
        payload,
        jwt_token.settings.SECRET_KEY,
        algorithm=jwt_token.settings.ALGORITHM,
    )
