from fastapi import Depends, HTTPException, Request, status
from jose import JWTError, jwt
from sqlmodel.ext.asyncio.session import AsyncSession

from app.config import settings
from app.database import get_session
from app.models.user import User
from app.services import auth_service, user_service


async def get_current_user(
    request: Request,
    session: AsyncSession = Depends(get_session),
) -> User:
    token = request.cookies.get("access_token") or request.cookies.get("id_token")

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )

    email: str | None = None

    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=["HS256"])
        email = payload.get("sub")
    except JWTError:
        pass

    if not email:
        try:
            claims = await auth_service.validate_cognito_id_token(token)
            email = claims.get("email")
        except (JWTError, ValueError):
            pass

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
