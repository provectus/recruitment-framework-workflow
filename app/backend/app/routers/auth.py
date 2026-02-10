import contextlib
import json
import secrets
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response, status
from fastapi.responses import RedirectResponse
from jose import jwt
from sqlmodel.ext.asyncio.session import AsyncSession

from app.config import settings
from app.database import get_session
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.schemas.auth import DevLoginRequest, StatusResponse, UserResponse
from app.services import auth_service, user_service

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/dev-login", response_model=UserResponse)
async def dev_login(
    request: DevLoginRequest,
    response: Response,
    session: AsyncSession = Depends(get_session),
) -> UserResponse:
    if not settings.debug:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")

    user = await user_service.create_or_update(
        session=session,
        email=request.email,
        full_name=request.name,
    )

    payload = {
        "sub": user.email,
        "name": user.full_name,
        "exp": datetime.now(UTC) + timedelta(minutes=30),
    }
    token = jwt.encode(payload, settings.jwt_secret_key, algorithm="HS256")

    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        path="/",
        samesite="lax",
        secure=settings.cookie_secure,
        domain=settings.cookie_domain,
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

    auth_state = {"state": state, "redirect": redirect or "/"}
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

    if not auth_state or auth_state.get("state") != state:
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
    if not email.endswith(f"@{settings.allowed_email_domain}"):
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

    redirect_path = auth_state.get("redirect", "/")
    redirect_response = RedirectResponse(
        url=redirect_path, status_code=status.HTTP_302_FOUND
    )

    redirect_response.set_cookie(
        key="access_token",
        value=tokens["access_token"],
        httponly=True,
        path="/",
        samesite="lax",
        secure=settings.cookie_secure,
        domain=settings.cookie_domain,
    )
    redirect_response.set_cookie(
        key="id_token",
        value=tokens["id_token"],
        httponly=True,
        path="/",
        samesite="lax",
        secure=settings.cookie_secure,
        domain=settings.cookie_domain,
    )

    if tokens.get("refresh_token"):
        redirect_response.set_cookie(
            key="refresh_token",
            value=tokens["refresh_token"],
            httponly=True,
            path="/",
            samesite="lax",
            secure=settings.cookie_secure,
            domain=settings.cookie_domain,
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
        samesite="lax",
        secure=settings.cookie_secure,
        domain=settings.cookie_domain,
    )
    response.set_cookie(
        key="id_token",
        value=tokens["id_token"],
        httponly=True,
        path="/",
        samesite="lax",
        secure=settings.cookie_secure,
        domain=settings.cookie_domain,
    )

    return StatusResponse(status="ok")


@router.post("/logout", response_model=StatusResponse)
async def logout(response: Response) -> StatusResponse:
    response.delete_cookie(key="access_token", path="/", domain=settings.cookie_domain)
    response.delete_cookie(key="id_token", path="/", domain=settings.cookie_domain)
    response.delete_cookie(key="refresh_token", path="/", domain=settings.cookie_domain)
    return StatusResponse(status="ok")
