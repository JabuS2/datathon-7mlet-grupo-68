import pytest
from fastapi import status

from schemas.user import UserCreate


@pytest.mark.asyncio
async def test_register_happy_path(client):
    user_data = UserCreate(
        email="newuser@example.com",
        password="strongpassword",
    )

    response = await client.post(
        "/register",
        json=user_data.model_dump(),
    )

    assert response.status_code == status.HTTP_200_OK

    data = response.json()
    assert data["email"] == user_data.email


@pytest.mark.asyncio
async def test_register_duplicate_email(client):
    user_data = UserCreate(
        email="duplicate@example.com",
        password="password123",
    )

    payload = user_data.model_dump()

    resp1 = await client.post("/register", json=payload)
    resp2 = await client.post("/register", json=payload)

    assert resp1.status_code == status.HTTP_200_OK
    assert resp2.status_code == status.HTTP_409_CONFLICT


@pytest.mark.asyncio
async def test_login_happy_path(client):
    user_data = UserCreate(
        email="test@example.com",
        password="password123",
    )

    await client.post("/register", json=user_data.model_dump())

    payload = user_data.model_dump()
    resp = await client.post("/login", json=payload)

    assert resp.status_code == status.HTTP_200_OK


@pytest.mark.asyncio
async def test_login_invalid_credentials(client):
    user_data = UserCreate(
        email="",
        password="",
    )

    payload = user_data.model_dump()
    resp = await client.post("/login", json=payload)

    assert resp.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.asyncio
async def test_me_endpoint(client):
    user_data = UserCreate(
        email="test@example.com",
        password="password123",
    )

    await client.post("/register", json=user_data.model_dump())

    payload = user_data.model_dump()
    resp = await client.post("/login", json=payload)

    assert resp.status_code == status.HTTP_200_OK

    me_resp = await client.get(
        "/me", headers={"Authorization": f"Bearer {resp.json()['accessToken']}"}
    )
    assert me_resp.status_code == status.HTTP_200_OK


@pytest.mark.asyncio
async def test_me_endpoint_unauthorized(client):
    me_resp = await client.get("/me")
    assert me_resp.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.asyncio
async def test_me_endpoint_invalid_token(client):
    me_resp = await client.get("/me", headers={"Authorization": "Bearer invalidtoken"})
    assert me_resp.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.asyncio
async def test_me_endpoint_expired_token(client, expired_token):
    me_resp = await client.get("/me", headers={"Authorization": f"Bearer {expired_token}"})
    assert me_resp.status_code == status.HTTP_401_UNAUTHORIZED
