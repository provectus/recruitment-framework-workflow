import pytest
from httpx import AsyncClient
from sqlmodel.ext.asyncio.session import AsyncSession

from app.dependencies.auth import get_current_user
from app.main import app
from app.models.user import User


@pytest.fixture(autouse=True)
def override_auth():
    mock_user = User(
        id=1,
        email="test@provectus.com",
        google_id="test123",
        full_name="Test User",
    )
    app.dependency_overrides[get_current_user] = lambda: mock_user
    yield
    app.dependency_overrides.pop(get_current_user, None)


async def test_list_users_empty(client: AsyncClient):
    response = await client.get("/api/users")
    assert response.status_code == 200
    assert response.json() == []


async def test_list_users(client: AsyncClient, session: AsyncSession):
    user1 = User(
        email="alice@provectus.com",
        google_id="alice123",
        full_name="Alice Smith",
    )
    user2 = User(
        email="bob@provectus.com",
        google_id="bob123",
        full_name="Bob Jones",
    )
    session.add(user1)
    session.add(user2)
    await session.commit()

    response = await client.get("/api/users")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]["full_name"] == "Alice Smith"
    assert data[1]["full_name"] == "Bob Jones"
    assert "id" in data[0]
    assert "email" in data[0]


async def test_list_users_sorted_by_name(client: AsyncClient, session: AsyncSession):
    user1 = User(
        email="zoe@provectus.com",
        google_id="zoe123",
        full_name="Zoe Wilson",
    )
    user2 = User(
        email="alice@provectus.com",
        google_id="alice123",
        full_name="Alice Smith",
    )
    user3 = User(
        email="bob@provectus.com",
        google_id="bob123",
        full_name="Bob Jones",
    )
    session.add(user1)
    session.add(user2)
    session.add(user3)
    await session.commit()

    response = await client.get("/api/users")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 3
    assert data[0]["full_name"] == "Alice Smith"
    assert data[1]["full_name"] == "Bob Jones"
    assert data[2]["full_name"] == "Zoe Wilson"
