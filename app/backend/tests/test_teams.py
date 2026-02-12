import pytest
from httpx import AsyncClient
from sqlalchemy import update
from sqlmodel.ext.asyncio.session import AsyncSession

from app.dependencies.auth import get_current_user
from app.main import app
from app.models.position import Position
from app.models.team import Team
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


async def test_list_teams_empty(client: AsyncClient):
    response = await client.get("/api/teams")
    assert response.status_code == 200
    assert response.json() == []


async def test_create_team(client: AsyncClient):
    response = await client.post("/api/teams", json={"name": "Engineering"})
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Engineering"
    assert "id" in data


async def test_create_team_duplicate(client: AsyncClient):
    await client.post("/api/teams", json={"name": "Engineering"})
    response = await client.post("/api/teams", json={"name": "Engineering"})
    assert response.status_code == 409


async def test_create_team_duplicate_case_insensitive(client: AsyncClient):
    await client.post("/api/teams", json={"name": "Engineering"})
    response = await client.post("/api/teams", json={"name": "engineering"})
    assert response.status_code == 409


async def test_delete_team(client: AsyncClient):
    create_response = await client.post("/api/teams", json={"name": "Engineering"})
    team_id = create_response.json()["id"]

    delete_response = await client.delete(f"/api/teams/{team_id}")
    assert delete_response.status_code == 204

    list_response = await client.get("/api/teams")
    assert list_response.json() == []


async def test_delete_team_not_found(client: AsyncClient):
    response = await client.delete("/api/teams/9999")
    assert response.status_code == 404


async def test_delete_team_in_use(client: AsyncClient, session: AsyncSession):
    create_response = await client.post("/api/teams", json={"name": "Engineering"})
    team_id = create_response.json()["id"]

    user = User(
        email="hiring@provectus.com",
        google_id="hiring123",
        full_name="Hiring Manager",
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)

    position = Position(
        title="Test Position",
        team_id=team_id,
        hiring_manager_id=user.id,
        status="open",
    )
    session.add(position)
    await session.commit()

    delete_response = await client.delete(f"/api/teams/{team_id}")
    assert delete_response.status_code == 409


async def test_list_teams_excludes_archived(client: AsyncClient, session: AsyncSession):
    create_response = await client.post("/api/teams", json={"name": "Engineering"})
    team_id = create_response.json()["id"]

    update_statement = update(Team).where(Team.id == team_id).values(is_archived=True)
    await session.exec(update_statement)
    await session.commit()

    list_response = await client.get("/api/teams")
    assert list_response.json() == []


async def test_delete_team_blocked_by_archived_position(
    client: AsyncClient, session: AsyncSession
):
    create_response = await client.post("/api/teams", json={"name": "Engineering"})
    team_id = create_response.json()["id"]

    user = User(
        email="hiring@provectus.com",
        google_id="hiring123",
        full_name="Hiring Manager",
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)

    position = Position(
        title="Test Position",
        team_id=team_id,
        hiring_manager_id=user.id,
        status="open",
        is_archived=True,
    )
    session.add(position)
    await session.commit()

    delete_response = await client.delete(f"/api/teams/{team_id}")
    assert delete_response.status_code == 409
