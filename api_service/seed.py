"""Idempotent database seed.

Creates a default admin account and a set of fake users so the stack is
usable right after the database is created (e.g. on first `docker compose up`).

Run manually with:  python seed.py
It is safe to run repeatedly: existing accounts (matched by email) are skipped.
"""

import asyncio

from core.jwt_token import JwtToken
from db.session import db
from db.unit_of_work import UnitOfWork
from models.user import User

ADMIN_EMAIL = "admin@admin.com"
ADMIN_PASSWORD = "admin123"

FAKE_USER_PASSWORD = "password123"
FAKE_USER_EMAILS = [
    "alice.johnson@example.com",
    "bruno.silva@example.com",
    "carla.mendes@example.com",
    "david.oliveira@example.com",
    "elena.costa@example.com",
    "felipe.rocha@example.com",
    "giovana.lima@example.com",
    "henrique.alves@example.com",
    "isabela.souza@example.com",
    "joao.pereira@example.com",
]


async def _ensure_user(
    uow: UnitOfWork,
    jwt: JwtToken,
    email: str,
    password: str,
    *,
    is_admin: bool,
) -> bool:
    """Create the user if it does not exist yet. Returns True if created."""
    existing = await uow.users.get_by_email(email)
    if existing is not None:
        return False

    uow.users.add(
        User(
            email=email,
            hashed_password=jwt.hash_password(password),
            is_admin=is_admin,
        )
    )
    return True


async def seed() -> None:
    jwt = JwtToken()

    async for session in db.session():
        async with UnitOfWork(session) as uow:
            admin_created = await _ensure_user(
                uow, jwt, ADMIN_EMAIL, ADMIN_PASSWORD, is_admin=True
            )

            fake_created = 0
            for email in FAKE_USER_EMAILS:
                if await _ensure_user(uow, jwt, email, FAKE_USER_PASSWORD, is_admin=False):
                    fake_created += 1

        print(
            f"Seed complete: admin {'created' if admin_created else 'already existed'} "
            f"({ADMIN_EMAIL}), {fake_created} fake user(s) created "
            f"({len(FAKE_USER_EMAILS) - fake_created} already existed)."
        )
        break

    await db.dispose()


if __name__ == "__main__":
    asyncio.run(seed())
