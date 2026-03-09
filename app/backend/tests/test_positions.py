import pytest
from httpx import AsyncClient
from sqlmodel.ext.asyncio.session import AsyncSession

from app.dependencies.auth import get_current_user
from app.main import app
from app.models.candidate import Candidate
from app.models.candidate_position import CandidatePosition
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


@pytest.fixture
async def team(session: AsyncSession) -> Team:
    team = Team(name="Engineering")
    session.add(team)
    await session.commit()
    await session.refresh(team)
    return team


@pytest.fixture
async def user(session: AsyncSession) -> User:
    user = User(email="hm@provectus.com", google_id="hm123", full_name="Hiring Manager")
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user


async def test_list_positions_empty(client: AsyncClient):
    response = await client.get("/api/positions")
    assert response.status_code == 200
    data = response.json()
    assert data == {"items": [], "total": 0, "offset": 0, "limit": 20}


async def test_create_position(client: AsyncClient, team: Team, user: User):
    response = await client.post(
        "/api/positions",
        json={
            "title": "Senior Backend Engineer",
            "requirements": "Python, FastAPI",
            "team_id": team.id,
            "hiring_manager_id": user.id,
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Senior Backend Engineer"
    assert data["requirements"] == "Python, FastAPI"
    assert data["status"] == "open"
    assert data["team_id"] == team.id
    assert data["hiring_manager_id"] == user.id
    assert data["is_archived"] is False
    assert "id" in data


async def test_create_position_missing_title(
    client: AsyncClient, team: Team, user: User
):
    response = await client.post(
        "/api/positions",
        json={
            "team_id": team.id,
            "hiring_manager_id": user.id,
        },
    )
    assert response.status_code == 422


async def test_create_position_invalid_team(client: AsyncClient, user: User):
    response = await client.post(
        "/api/positions",
        json={
            "title": "Senior Backend Engineer",
            "team_id": 9999,
            "hiring_manager_id": user.id,
        },
    )
    assert response.status_code == 404
    assert "Team not found" in response.json()["detail"]


async def test_create_position_invalid_hiring_manager(client: AsyncClient, team: Team):
    response = await client.post(
        "/api/positions",
        json={
            "title": "Senior Backend Engineer",
            "team_id": team.id,
            "hiring_manager_id": 9999,
        },
    )
    assert response.status_code == 404
    assert "Hiring manager not found" in response.json()["detail"]


async def test_list_positions_with_data(
    client: AsyncClient, session: AsyncSession, team: Team, user: User
):
    position1 = Position(
        title="Senior Backend Engineer",
        team_id=team.id,
        hiring_manager_id=user.id,
        status="open",
    )
    position2 = Position(
        title="Frontend Engineer",
        team_id=team.id,
        hiring_manager_id=user.id,
        status="open",
    )
    session.add(position1)
    session.add(position2)
    await session.commit()

    response = await client.get("/api/positions")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2
    assert len(data["items"]) == 2
    assert data["items"][0]["team_name"] == "Engineering"
    assert data["items"][0]["hiring_manager_name"] == "Hiring Manager"
    assert data["items"][0]["candidate_count"] == 0


async def test_list_positions_pagination(
    client: AsyncClient, session: AsyncSession, team: Team, user: User
):
    for i in range(3):
        position = Position(
            title=f"Position {i + 1}",
            team_id=team.id,
            hiring_manager_id=user.id,
            status="open",
        )
        session.add(position)
    await session.commit()

    response = await client.get("/api/positions?limit=2")
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 2
    assert data["total"] == 3
    assert data["limit"] == 2


async def test_list_positions_with_candidates(
    client: AsyncClient, session: AsyncSession, team: Team, user: User
):
    position = Position(
        title="Senior Backend Engineer",
        team_id=team.id,
        hiring_manager_id=user.id,
        status="open",
    )
    session.add(position)
    await session.commit()
    await session.refresh(position)

    candidate1 = Candidate(
        full_name="John Doe",
        email="john@example.com",
    )
    candidate2 = Candidate(
        full_name="Jane Smith",
        email="jane@example.com",
    )
    session.add(candidate1)
    session.add(candidate2)
    await session.commit()
    await session.refresh(candidate1)
    await session.refresh(candidate2)

    cp1 = CandidatePosition(
        candidate_id=candidate1.id,
        position_id=position.id,
        stage="new",
    )
    cp2 = CandidatePosition(
        candidate_id=candidate2.id,
        position_id=position.id,
        stage="screening",
    )
    session.add(cp1)
    session.add(cp2)
    await session.commit()

    response = await client.get("/api/positions")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["candidate_count"] == 2


async def test_get_position_detail(
    client: AsyncClient, session: AsyncSession, team: Team, user: User
):
    position = Position(
        title="Senior Backend Engineer",
        requirements="Python, FastAPI, async",
        team_id=team.id,
        hiring_manager_id=user.id,
        status="open",
    )
    session.add(position)
    await session.commit()
    await session.refresh(position)

    response = await client.get(f"/api/positions/{position.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == position.id
    assert data["title"] == "Senior Backend Engineer"
    assert data["requirements"] == "Python, FastAPI, async"
    assert data["status"] == "open"
    assert data["team_id"] == team.id
    assert data["team_name"] == "Engineering"
    assert data["hiring_manager_id"] == user.id
    assert data["hiring_manager_name"] == "Hiring Manager"
    assert data["is_archived"] is False
    assert data["candidates"] == []
    assert "created_at" in data
    assert "updated_at" in data


async def test_get_position_not_found(client: AsyncClient):
    response = await client.get("/api/positions/9999")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


async def test_update_position_title(
    client: AsyncClient, session: AsyncSession, team: Team, user: User
):
    position = Position(
        title="Senior Backend Engineer",
        team_id=team.id,
        hiring_manager_id=user.id,
        status="open",
    )
    session.add(position)
    await session.commit()
    await session.refresh(position)

    response = await client.patch(
        f"/api/positions/{position.id}",
        json={"title": "Staff Backend Engineer"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Staff Backend Engineer"
    assert data["status"] == "open"


async def test_update_position_status(
    client: AsyncClient, session: AsyncSession, team: Team, user: User
):
    position = Position(
        title="Senior Backend Engineer",
        team_id=team.id,
        hiring_manager_id=user.id,
        status="open",
    )
    session.add(position)
    await session.commit()
    await session.refresh(position)

    response = await client.patch(
        f"/api/positions/{position.id}",
        json={"status": "on_hold"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "on_hold"


async def test_update_position_invalid_status(
    client: AsyncClient, session: AsyncSession, team: Team, user: User
):
    position = Position(
        title="Senior Backend Engineer",
        team_id=team.id,
        hiring_manager_id=user.id,
        status="open",
    )
    session.add(position)
    await session.commit()
    await session.refresh(position)

    response = await client.patch(
        f"/api/positions/{position.id}",
        json={"status": "invalid_status"},
    )
    assert response.status_code == 422
    assert "Invalid status" in response.json()["detail"]


async def test_list_positions_filter_by_status(
    client: AsyncClient, session: AsyncSession, team: Team, user: User
):
    position1 = Position(
        title="Position 1",
        team_id=team.id,
        hiring_manager_id=user.id,
        status="open",
    )
    position2 = Position(
        title="Position 2",
        team_id=team.id,
        hiring_manager_id=user.id,
        status="on_hold",
    )
    position3 = Position(
        title="Position 3",
        team_id=team.id,
        hiring_manager_id=user.id,
        status="open",
    )
    session.add(position1)
    session.add(position2)
    session.add(position3)
    await session.commit()

    response = await client.get("/api/positions?status=open")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2
    assert len(data["items"]) == 2
    for item in data["items"]:
        assert item["status"] == "open"


async def test_list_positions_filter_by_team(
    client: AsyncClient, session: AsyncSession, team: Team, user: User
):
    team2 = Team(name="Product")
    session.add(team2)
    await session.commit()
    await session.refresh(team2)

    position1 = Position(
        title="Position 1",
        team_id=team.id,
        hiring_manager_id=user.id,
        status="open",
    )
    position2 = Position(
        title="Position 2",
        team_id=team2.id,
        hiring_manager_id=user.id,
        status="open",
    )
    position3 = Position(
        title="Position 3",
        team_id=team.id,
        hiring_manager_id=user.id,
        status="open",
    )
    session.add(position1)
    session.add(position2)
    session.add(position3)
    await session.commit()

    response = await client.get(f"/api/positions?team_id={team.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2
    assert len(data["items"]) == 2
    for item in data["items"]:
        assert item["team_name"] == "Engineering"


async def test_archive_position(
    client: AsyncClient, session: AsyncSession, team: Team, user: User
):
    position = Position(
        title="Senior Backend Engineer",
        team_id=team.id,
        hiring_manager_id=user.id,
        status="open",
    )
    session.add(position)
    await session.commit()
    await session.refresh(position)

    response = await client.post(f"/api/positions/{position.id}/archive")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == position.id
    assert data["title"] == "Senior Backend Engineer"
    assert data["status"] == "open"
    assert data["is_archived"] is True


async def test_archive_position_hidden_from_list(
    client: AsyncClient, session: AsyncSession, team: Team, user: User
):
    position = Position(
        title="Senior Backend Engineer",
        team_id=team.id,
        hiring_manager_id=user.id,
        status="open",
    )
    session.add(position)
    await session.commit()
    await session.refresh(position)

    await client.post(f"/api/positions/{position.id}/archive")

    response = await client.get("/api/positions")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 0
    assert len(data["items"]) == 0


async def test_archive_position_not_found(client: AsyncClient):
    response = await client.post("/api/positions/99999/archive")
    assert response.status_code == 404
    assert "Position not found" in response.json()["detail"]
