import logging

import jwt
from fastapi import Depends, HTTPException, Request, status
from jwt.exceptions import InvalidTokenError
from sqlmodel.ext.asyncio.session import AsyncSession

from app.config import settings
from app.database import get_session
from app.models.user import User
from app.services import auth_service, user_service

logger = logging.getLogger(__name__)


async def get_current_user(
    request: Request,
    session: AsyncSession = Depends(get_session),
) -> User:
    access_token = request.cookies.get("access_token")
    id_token_cookie = request.cookies.get("id_token")

    if not access_token and not id_token_cookie:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )

    email: str | None = None

    if access_token:
        try:
            payload = jwt.decode(
                access_token, settings.jwt_secret_key, algorithms=["HS256"]
            )
            email = payload.get("sub")
        except InvalidTokenError:
            pass

    if not email and id_token_cookie and not settings.debug:
        try:
            claims = await auth_service.validate_cognito_id_token(id_token_cookie)
            email = claims.get("email")
        except Exception:
            logger.warning("Cognito token validation failed", exc_info=True)

    if not email:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
        )

    user = await user_service.get_by_email(session, email)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    return user
