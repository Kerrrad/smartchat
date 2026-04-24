import pytest


@pytest.mark.asyncio
async def test_register_and_login(async_client):
    register_response = await async_client.post(
        "/api/v1/auth/register",
        json={
            "email": "ewa@example.com",
            "username": "ewa",
            "password": "Password123!",
        },
    )
    assert register_response.status_code == 201
    assert register_response.json()["username"] == "ewa"

    login_response = await async_client.post(
        "/api/v1/auth/login",
        json={"login": "ewa", "password": "Password123!"},
    )
    assert login_response.status_code == 200
    payload = login_response.json()
    assert payload["access_token"]
    assert payload["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_profile_bio_limit(async_client, seeded_data, auth_headers):
    too_long_bio = "x" * 41
    too_long_response = await async_client.patch(
        "/api/v1/users/me",
        json={"bio": too_long_bio},
        headers=auth_headers(seeded_data["alice_token"]),
    )
    assert too_long_response.status_code == 422

    valid_bio = "Krotkie bio do profilu testowego."
    valid_response = await async_client.patch(
        "/api/v1/users/me",
        json={"bio": valid_bio},
        headers=auth_headers(seeded_data["alice_token"]),
    )
    assert valid_response.status_code == 200
    assert valid_response.json()["bio"] == valid_bio
