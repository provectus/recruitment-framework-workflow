import os
from collections.abc import AsyncGenerator

os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key-for-tests-only-32chars")

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession

from app.database import get_session
from app.dependencies.auth import get_current_user
from app.main import app
from app.models.candidate import Candidate
from app.models.candidate_position import CandidatePosition
from app.models.position import Position
from app.models.team import Team
from app.models.user import User

TEST_DATABASE_URL = "sqlite+aiosqlite:///./test.db"

engine = create_async_engine(
    TEST_DATABASE_URL,
    echo=True,
    connect_args={"check_same_thread": False},
)

async_session_factory = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


@pytest.fixture(autouse=True)
async def setup_database():
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)


@pytest.fixture
async def session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_factory() as session:
        yield session


@pytest.fixture
async def client(session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    async def get_session_override():
        yield session

    app.dependency_overrides[get_session] = get_session_override

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        yield client

    app.dependency_overrides.clear()


@pytest.fixture
async def test_user(session: AsyncSession) -> User:
    user = User(
        email="test@example.com",
        google_id="test-google-id",
        full_name="Test User",
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user


@pytest.fixture
async def authenticated_client(
    session: AsyncSession,
    test_user: User,
) -> AsyncGenerator[AsyncClient, None]:
    async def get_session_override() -> AsyncGenerator[AsyncSession, None]:
        yield session

    async def get_current_user_override() -> User:
        return test_user

    app.dependency_overrides[get_session] = get_session_override
    app.dependency_overrides[get_current_user] = get_current_user_override

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        yield client

    app.dependency_overrides.clear()


@pytest.fixture
async def candidate_position(
    session: AsyncSession, test_user: User
) -> CandidatePosition:
    candidate = Candidate(full_name="Alice Johnson", email="alice@example.com")
    session.add(candidate)
    await session.flush()

    team = Team(name="Engineering")
    session.add(team)
    await session.flush()

    position = Position(
        title="Backend Engineer",
        team_id=team.id,
        hiring_manager_id=test_user.id,
        status="open",
    )
    session.add(position)
    await session.flush()

    cp = CandidatePosition(
        candidate_id=candidate.id,
        position_id=position.id,
        stage="new",
    )
    session.add(cp)
    await session.commit()
    await session.refresh(cp)
    return cp
