import pytest
from fastapi import status
from sqlalchemy import text

from schemas.user import UserCreate


async def _register_and_login(client, email: str, password: str = "supersecret123") -> str:
    user_data = UserCreate(email=email, password=password)
    await client.post("/register", json=user_data.model_dump())
    resp = await client.post("/login", json=user_data.model_dump())
    assert resp.status_code == status.HTTP_200_OK
    return str(resp.json()["accessToken"])


async def _promote_to_admin(db_session, email: str) -> None:
    await db_session.execute(
        text("UPDATE users SET is_admin = true WHERE email = :email"),
        {"email": email},
    )
    await db_session.commit()


@pytest.mark.asyncio
async def test_users_overview_requires_authentication(client):
    resp = await client.get("/admin/users/overview")
    assert resp.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.asyncio
async def test_users_overview_forbidden_for_non_admin(client):
    token = await _register_and_login(client, "normal@example.com")

    resp = await client.get(
        "/admin/users/overview",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert resp.status_code == status.HTTP_403_FORBIDDEN
    assert resp.json()["code"] == "ADMIN_REQUIRED"


@pytest.mark.asyncio
async def test_users_overview_as_admin(client, db_session):
    token = await _register_and_login(client, "admin@example.com")
    await _promote_to_admin(db_session, "admin@example.com")

    resp = await client.get(
        "/admin/users/overview",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert resp.status_code == status.HTTP_200_OK

    data = resp.json()
    assert data["totalUsers"] == 1
    assert data["adminCount"] == 1
    assert data["signupsLast7Days"] == 1
    assert data["signupsLast30Days"] == 1
    assert len(data["latestUsers"]) == 1
    assert data["latestUsers"][0]["email"] == "admin@example.com"
    assert data["latestUsers"][0]["isAdmin"] is True
