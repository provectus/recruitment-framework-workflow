import contextlib
import hmac
import json
import secrets
from datetime import UTC, datetime, timedelta

import jwt
from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response, status
from fastapi.responses import RedirectResponse
from sqlmodel.ext.asyncio.session import AsyncSession

from app.config import settings
from app.database import get_session
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.schemas.auth import DevLoginRequest, StatusResponse, UserResponse
from app.services import auth_service, user_service

router = APIRouter(prefix="/api/auth", tags=["auth"])

ACCESS_TOKEN_MAX_AGE = 3600
REFRESH_TOKEN_MAX_AGE = 30 * 24 * 3600


def _safe_redirect_path(url: str | None) -> str:
    if not url or not url.startswith("/") or url.startswith("//") or "\\" in url:
        return "/"
    return url


@router.post("/dev-login", response_model=UserResponse)
async def dev_login(
    request: DevLoginRequest,
    response: Response,
    session: AsyncSession = Depends(get_session),
) -> UserResponse:
    if not settings.debug:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")

    email_domain = request.email.rsplit("@", 1)[-1] if "@" in request.email else ""
    if email_domain != settings.allowed_email_domain:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email domain not allowed",
        )

    user = await user_service.create_or_update(
        session=session,
        email=request.email,
        full_name=request.name,
    )

    payload = {
        "sub": user.email,
        "name": user.full_name,
        "exp": datetime.now(UTC) + timedelta(seconds=ACCESS_TOKEN_MAX_AGE),
    }
    token = jwt.encode(payload, settings.jwt_secret_key, algorithm="HS256")

    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        path="/",
        samesite="strict",
        secure=settings.cookie_secure,
        domain=settings.cookie_domain,
        max_age=ACCESS_TOKEN_MAX_AGE,
    )

    return UserResponse(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        avatar_url=user.avatar_url,
    )


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)) -> UserResponse:
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        full_name=current_user.full_name,
        avatar_url=current_user.avatar_url,
    )


@router.get("/login", include_in_schema=False)
async def login(redirect: str | None = Query(default=None)) -> RedirectResponse:
    state = secrets.token_urlsafe(32)

    auth_state = {"state": state, "redirect": _safe_redirect_path(redirect)}
    cognito_url = await auth_service.build_cognito_auth_url(
        redirect_path=redirect, state=state
    )

    redirect_response = RedirectResponse(
        url=cognito_url, status_code=status.HTTP_302_FOUND
    )
    redirect_response.set_cookie(
        key="auth_state",
        value=json.dumps(auth_state),
        httponly=True,
        path="/",
        samesite="lax",
        secure=settings.cookie_secure,
        domain=settings.cookie_domain,
        max_age=300,
    )

    return redirect_response


@router.get("/callback", include_in_schema=False)
async def callback(
    request: Request,
    code: str = Query(),
    state: str = Query(),
    session: AsyncSession = Depends(get_session),
) -> RedirectResponse:
    auth_state_cookie = request.cookies.get("auth_state")
    auth_state = None

    with contextlib.suppress(json.JSONDecodeError):
        auth_state = json.loads(auth_state_cookie) if auth_state_cookie else None

    stored_state = auth_state.get("state", "") if auth_state else ""
    if not auth_state or not hmac.compare_digest(stored_state, state):
        return RedirectResponse(
            url="/login?error=invalid_state", status_code=status.HTTP_302_FOUND
        )

    try:
        tokens = await auth_service.exchange_code_for_tokens(code)
        claims = await auth_service.validate_cognito_id_token(tokens["id_token"])
    except Exception:
        return RedirectResponse(
            url="/login?error=auth_failed", status_code=status.HTTP_302_FOUND
        )

    email = claims.get("email", "")
    email_domain = email.rsplit("@", 1)[-1] if "@" in email else ""
    if email_domain != settings.allowed_email_domain:
        redirect_response = RedirectResponse(
            url="/login?error=domain_restricted", status_code=status.HTTP_302_FOUND
        )
        redirect_response.delete_cookie(key="auth_state", path="/")
        return redirect_response

    await user_service.create_or_update(
        session=session,
        email=email,
        full_name=claims.get("name", ""),
        avatar_url=claims.get("picture"),
        google_id=claims.get("sub", ""),
    )

    redirect_path = _safe_redirect_path(auth_state.get("redirect"))
    redirect_response = RedirectResponse(
        url=redirect_path, status_code=status.HTTP_302_FOUND
    )

    app_token_payload = {
        "sub": email,
        "name": claims.get("name", ""),
        "exp": datetime.now(UTC) + timedelta(seconds=ACCESS_TOKEN_MAX_AGE),
    }
    app_token = jwt.encode(
        app_token_payload, settings.jwt_secret_key, algorithm="HS256"
    )

    redirect_response.set_cookie(
        key="access_token",
        value=app_token,
        httponly=True,
        path="/",
        samesite="strict",
        secure=settings.cookie_secure,
        domain=settings.cookie_domain,
        max_age=ACCESS_TOKEN_MAX_AGE,
    )
    redirect_response.set_cookie(
        key="id_token",
        value=tokens["id_token"],
        httponly=True,
        path="/",
        samesite="strict",
        secure=settings.cookie_secure,
        domain=settings.cookie_domain,
        max_age=ACCESS_TOKEN_MAX_AGE,
    )

    if tokens.get("refresh_token"):
        redirect_response.set_cookie(
            key="refresh_token",
            value=tokens["refresh_token"],
            httponly=True,
            path="/",
            samesite="strict",
            secure=settings.cookie_secure,
            domain=settings.cookie_domain,
            max_age=REFRESH_TOKEN_MAX_AGE,
        )

    redirect_response.delete_cookie(key="auth_state", path="/")

    return redirect_response


@router.post("/refresh", response_model=StatusResponse)
async def refresh(request: Request, response: Response) -> StatusResponse:
    refresh_token_value = request.cookies.get("refresh_token")
    if not refresh_token_value:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="No refresh token"
        )

    try:
        tokens = await auth_service.refresh_tokens(refresh_token_value)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh failed"
        ) from None

    response.set_cookie(
        key="access_token",
        value=tokens["access_token"],
        httponly=True,
        path="/",
        samesite="strict",
        secure=settings.cookie_secure,
        domain=settings.cookie_domain,
        max_age=ACCESS_TOKEN_MAX_AGE,
    )
    response.set_cookie(
        key="id_token",
        value=tokens["id_token"],
        httponly=True,
        path="/",
        samesite="strict",
        secure=settings.cookie_secure,
        domain=settings.cookie_domain,
        max_age=ACCESS_TOKEN_MAX_AGE,
    )

    return StatusResponse(status="ok")


@router.post("/logout", response_model=StatusResponse)
async def logout(response: Response) -> StatusResponse:
    cookie_opts = {
        "path": "/",
        "domain": settings.cookie_domain,
        "samesite": "strict",
        "secure": settings.cookie_secure,
        "httponly": True,
    }
    response.delete_cookie(key="access_token", **cookie_opts)
    response.delete_cookie(key="id_token", **cookie_opts)
    response.delete_cookie(key="refresh_token", **cookie_opts)
    return StatusResponse(status="ok")
