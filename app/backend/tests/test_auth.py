import json
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient
from jose import jwt

from app.config import settings
from app.services import auth_service


@pytest.mark.asyncio
async def test_health_check_still_works(client: AsyncClient):
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@pytest.mark.asyncio
async def test_dev_login_creates_user_and_sets_cookie(client: AsyncClient):
    with patch.object(settings, "debug", True):
        response = await client.post(
            "/auth/dev-login",
            json={"email": "test@provectus.com", "name": "Test User"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "test@provectus.com"
        assert data["full_name"] == "Test User"
        assert data["avatar_url"] is None
        assert "id" in data

        assert "access_token" in response.cookies


@pytest.mark.asyncio
async def test_dev_login_updates_existing_user(client: AsyncClient):
    with patch.object(settings, "debug", True):
        response1 = await client.post(
            "/auth/dev-login",
            json={"email": "test@provectus.com", "name": "Test User"},
        )
        assert response1.status_code == 200
        user_id = response1.json()["id"]

        response2 = await client.post(
            "/auth/dev-login",
            json={"email": "test@provectus.com", "name": "Updated User"},
        )
        assert response2.status_code == 200
        assert response2.json()["id"] == user_id
        assert response2.json()["full_name"] == "Updated User"


@pytest.mark.asyncio
async def test_auth_me_with_valid_cookie(client: AsyncClient):
    with patch.object(settings, "debug", True):
        login_response = await client.post(
            "/auth/dev-login",
            json={"email": "test@provectus.com", "name": "Test User"},
        )
        assert login_response.status_code == 200

        me_response = await client.get("/auth/me")
        assert me_response.status_code == 200
        data = me_response.json()
        assert data["email"] == "test@provectus.com"
        assert data["full_name"] == "Test User"


@pytest.mark.asyncio
async def test_auth_me_with_no_cookie(client: AsyncClient):
    response = await client.get("/auth/me")
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"


@pytest.mark.asyncio
async def test_auth_me_with_expired_cookie(client: AsyncClient):
    with (
        patch.object(settings, "debug", True),
        patch.object(
            auth_service,
            "validate_cognito_id_token",
            new_callable=AsyncMock,
            side_effect=ValueError("Invalid token"),
        ),
    ):
        login_response = await client.post(
            "/auth/dev-login",
            json={"email": "test@provectus.com", "name": "Test User"},
        )
        assert login_response.status_code == 200

        expired_payload = {
            "sub": "test@provectus.com",
            "name": "Test User",
            "exp": datetime.now(UTC) - timedelta(minutes=1),
        }
        expired_token = jwt.encode(
            expired_payload, settings.jwt_secret_key, algorithm="HS256"
        )

        client.cookies.set("access_token", expired_token)

        response = await client.get("/auth/me")
        assert response.status_code == 401
        assert response.json()["detail"] == "Invalid authentication credentials"


@pytest.mark.asyncio
async def test_auth_me_with_invalid_cookie(client: AsyncClient):
    client.cookies.set("access_token", "invalid_token")

    response = await client.get("/auth/me")
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid authentication credentials"


@pytest.mark.asyncio
async def test_dev_login_when_debug_false(client: AsyncClient):
    with patch.object(settings, "debug", False):
        response = await client.post(
            "/auth/dev-login",
            json={"email": "test@provectus.com", "name": "Test User"},
        )
        assert response.status_code == 404


@pytest.mark.asyncio
async def test_login_redirects_to_cognito(client: AsyncClient):
    with (
        patch.object(
            settings, "cognito_domain", "test.auth.us-east-1.amazoncognito.com"
        ),
        patch.object(settings, "cognito_client_id", "test_client_id"),
    ):
        response = await client.get("/auth/login", follow_redirects=False)
        assert response.status_code == 302
        location = response.headers["location"]
        assert "test.auth.us-east-1.amazoncognito.com" in location
        assert "response_type=code" in location
        assert "client_id=test_client_id" in location

        set_cookie_header = response.headers.get("set-cookie", "")
        assert "auth_state" in set_cookie_header


@pytest.mark.asyncio
async def test_callback_happy_path(client: AsyncClient):
    with (
        patch.object(
            auth_service,
            "exchange_code_for_tokens",
            new_callable=AsyncMock,
        ) as mock_exchange,
        patch.object(
            auth_service,
            "validate_cognito_id_token",
            new_callable=AsyncMock,
        ) as mock_validate,
    ):
        mock_exchange.return_value = {
            "access_token": "test_access_token",
            "id_token": "test_id_token",
            "refresh_token": "test_refresh_token",
        }
        mock_validate.return_value = {
            "sub": "google123",
            "email": "user@provectus.com",
            "name": "Test User",
            "picture": "https://example.com/avatar.jpg",
        }

        test_state = "test_state_value"
        auth_state = {"state": test_state, "redirect": "/dashboard"}
        client.cookies.set("auth_state", json.dumps(auth_state))

        response = await client.get(
            f"/auth/callback?code=test_code&state={test_state}",
            follow_redirects=False,
        )

        assert response.status_code == 302
        assert response.headers["location"] == "/dashboard"

        set_cookie_headers = response.headers.get_list("set-cookie")
        cookie_names = [h.split("=")[0] for h in set_cookie_headers]
        assert "access_token" in cookie_names
        assert "id_token" in cookie_names
        assert "refresh_token" in cookie_names

        me_response = await client.get("/auth/me")
        assert me_response.status_code == 200
        assert me_response.json()["email"] == "user@provectus.com"


@pytest.mark.asyncio
async def test_callback_domain_rejection(client: AsyncClient):
    with (
        patch.object(
            auth_service,
            "exchange_code_for_tokens",
            new_callable=AsyncMock,
        ) as mock_exchange,
        patch.object(
            auth_service,
            "validate_cognito_id_token",
            new_callable=AsyncMock,
        ) as mock_validate,
    ):
        mock_exchange.return_value = {
            "access_token": "test_access_token",
            "id_token": "test_id_token",
        }
        mock_validate.return_value = {
            "sub": "google123",
            "email": "user@wrongdomain.com",
            "name": "Test User",
            "picture": None,
        }

        test_state = "test_state_value"
        auth_state = {"state": test_state, "redirect": "/"}
        client.cookies.set("auth_state", json.dumps(auth_state))

        response = await client.get(
            f"/auth/callback?code=test_code&state={test_state}",
            follow_redirects=False,
        )

        assert response.status_code == 302
        assert "domain_restricted" in response.headers["location"]

        me_response = await client.get("/auth/me")
        assert me_response.status_code == 401


@pytest.mark.asyncio
async def test_callback_invalid_state(client: AsyncClient):
    auth_state = {"state": "correct_state", "redirect": "/"}
    client.cookies.set("auth_state", json.dumps(auth_state))

    response = await client.get(
        "/auth/callback?code=test_code&state=wrong_state", follow_redirects=False
    )

    assert response.status_code == 302
    assert "invalid_state" in response.headers["location"]


@pytest.mark.asyncio
async def test_logout_clears_cookies(client: AsyncClient):
    with patch.object(settings, "debug", True):
        login_response = await client.post(
            "/auth/dev-login",
            json={"email": "test@provectus.com", "name": "Test User"},
        )
        assert login_response.status_code == 200

    me_response = await client.get("/auth/me")
    assert me_response.status_code == 200
    assert me_response.json()["email"] == "test@provectus.com"

    logout_response = await client.post("/auth/logout")
    assert logout_response.status_code == 200
    assert logout_response.json() == {"status": "ok"}

    set_cookie_headers = logout_response.headers.get_list("set-cookie")
    cookie_names = [h.split("=")[0] for h in set_cookie_headers]
    assert "access_token" in cookie_names
    assert "id_token" in cookie_names
    assert "refresh_token" in cookie_names

    for header in set_cookie_headers:
        is_auth_cookie = (
            "access_token" in header
            or "id_token" in header
            or "refresh_token" in header
        )
        if is_auth_cookie:
            assert "Max-Age=0" in header or "max-age=0" in header.lower()


@pytest.mark.asyncio
async def test_logout_subsequent_me_returns_401(client: AsyncClient):
    with patch.object(settings, "debug", True):
        login_response = await client.post(
            "/auth/dev-login",
            json={"email": "test@provectus.com", "name": "Test User"},
        )
        assert login_response.status_code == 200

    me_response_before = await client.get("/auth/me")
    assert me_response_before.status_code == 200

    logout_response = await client.post("/auth/logout")
    assert logout_response.status_code == 200

    client.cookies.delete("access_token")
    client.cookies.delete("id_token")
    client.cookies.delete("refresh_token")

    me_response_after = await client.get("/auth/me")
    assert me_response_after.status_code == 401


@pytest.mark.asyncio
async def test_refresh_without_cookie_returns_401(client: AsyncClient):
    response = await client.post("/auth/refresh")
    assert response.status_code == 401
    assert response.json()["detail"] == "No refresh token"


@pytest.mark.asyncio
async def test_refresh_with_valid_token(client: AsyncClient):
    with patch.object(
        auth_service,
        "refresh_tokens",
        new_callable=AsyncMock,
    ) as mock_refresh:
        mock_refresh.return_value = {
            "access_token": "new_access_token",
            "id_token": "new_id_token",
        }

        client.cookies.set("refresh_token", "test_refresh_token")

        response = await client.post("/auth/refresh")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}

        set_cookie_headers = response.headers.get_list("set-cookie")
        cookie_names = [h.split("=")[0] for h in set_cookie_headers]
        assert "access_token" in cookie_names
        assert "id_token" in cookie_names

        mock_refresh.assert_called_once_with("test_refresh_token")


@pytest.mark.asyncio
async def test_refresh_with_expired_token(client: AsyncClient):
    with patch.object(
        auth_service,
        "refresh_tokens",
        new_callable=AsyncMock,
    ) as mock_refresh:
        mock_refresh.side_effect = Exception("Token expired")

        client.cookies.set("refresh_token", "expired_refresh_token")

        response = await client.post("/auth/refresh")
        assert response.status_code == 401
        assert response.json()["detail"] == "Refresh failed"
