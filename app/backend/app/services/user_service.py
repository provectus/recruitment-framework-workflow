from sqlalchemy import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models.user import User


async def get_by_email(session: AsyncSession, email: str) -> User | None:
    statement = select(User).where(User.email == email)
    result = await session.execute(statement)
    return result.scalar_one_or_none()


async def create_or_update(
    session: AsyncSession,
    email: str,
    full_name: str,
    avatar_url: str | None = None,
    google_id: str | None = None,
) -> User:
    user = await get_by_email(session, email)

    if user:
        user.full_name = full_name
        if avatar_url is not None:
            user.avatar_url = avatar_url
        session.add(user)
    else:
        user = User(
            email=email,
            full_name=full_name,
            avatar_url=avatar_url,
            google_id=google_id or f"dev_{email}",
        )
        session.add(user)

    await session.commit()
    await session.refresh(user)
    return user
