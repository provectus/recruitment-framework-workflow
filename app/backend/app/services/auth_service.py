import base64
import hashlib
import hmac
import secrets
from typing import Any
from urllib.parse import urlencode

import httpx
from jose import jwt

from app.config import settings

_jwks_cache: dict[str, Any] | None = None


async def build_cognito_auth_url(
    redirect_path: str | None = None, state: str | None = None
) -> str:
    if state is None:
        state = secrets.token_urlsafe(32)

    params = {
        "response_type": "code",
        "client_id": settings.cognito_client_id,
        "redirect_uri": settings.cognito_redirect_uri,
        "scope": "openid email profile",
        "state": state,
    }

    return f"https://{settings.cognito_domain}/oauth2/authorize?{urlencode(params)}"


async def exchange_code_for_tokens(code: str) -> dict[str, Any]:
    data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": settings.cognito_redirect_uri,
        "client_id": settings.cognito_client_id,
    }

    if settings.cognito_client_secret:
        data["client_secret"] = settings.cognito_client_secret

    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"https://{settings.cognito_domain}/oauth2/token",
            data=data,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        response.raise_for_status()
        result: dict[str, Any] = response.json()
        return result


async def get_jwks() -> dict[str, Any]:
    global _jwks_cache
    if _jwks_cache is not None:
        return _jwks_cache

    async with httpx.AsyncClient() as client:
        response = await client.get(settings.cognito_jwks_url)
        response.raise_for_status()
        _jwks_cache = response.json()
        return _jwks_cache


async def validate_cognito_id_token(id_token: str) -> dict[str, Any]:
    unverified_header = jwt.get_unverified_header(id_token)
    kid = unverified_header.get("kid")

    jwks = await get_jwks()
    key_dict = next((k for k in jwks["keys"] if k["kid"] == kid), None)
    if not key_dict:
        msg = "Public key not found in JWKS"
        raise ValueError(msg)

    public_key = {
        "kty": key_dict["kty"],
        "kid": key_dict["kid"],
        "use": key_dict["use"],
        "n": key_dict["n"],
        "e": key_dict["e"],
    }

    claims = jwt.decode(
        id_token,
        public_key,
        algorithms=["RS256"],
        audience=settings.cognito_client_id,
        issuer=settings.cognito_issuer,
    )

    return {
        "sub": claims.get("sub", ""),
        "email": claims.get("email", ""),
        "name": claims.get("name", ""),
        "picture": claims.get("picture"),
    }


def compute_secret_hash(username: str) -> str:
    message = username + settings.cognito_client_id
    dig = hmac.new(
        settings.cognito_client_secret.encode("utf-8"),
        msg=message.encode("utf-8"),
        digestmod=hashlib.sha256,
    ).digest()
    return base64.b64encode(dig).decode()


async def refresh_tokens(refresh_token: str) -> dict[str, Any]:
    data = {
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
        "client_id": settings.cognito_client_id,
    }

    if settings.cognito_client_secret:
        data["client_secret"] = settings.cognito_client_secret

    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"https://{settings.cognito_domain}/oauth2/token",
            data=data,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        response.raise_for_status()
        result: dict[str, Any] = response.json()
        return result
