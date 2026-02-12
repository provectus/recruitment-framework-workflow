import pytest
from httpx import AsyncClient
from sqlmodel.ext.asyncio.session import AsyncSession

from app.dependencies.auth import get_current_user
from app.main import app
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


async def test_list_candidates_empty(client: AsyncClient):
    response = await client.get("/api/candidates")
    assert response.status_code == 200
    data = response.json()
    assert data == {"items": [], "total": 0, "offset": 0, "limit": 20}


async def test_create_candidate(client: AsyncClient):
    response = await client.post(
        "/api/candidates",
        json={
            "full_name": "Alice Johnson",
            "email": "alice@example.com",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["full_name"] == "Alice Johnson"
    assert data["email"] == "alice@example.com"
    assert data["is_archived"] is False
    assert "id" in data


async def test_create_candidate_duplicate_email(client: AsyncClient):
    await client.post(
        "/api/candidates",
        json={
            "full_name": "Alice Johnson",
            "email": "alice@example.com",
        },
    )

    response = await client.post(
        "/api/candidates",
        json={
            "full_name": "Alice Smith",
            "email": "alice@example.com",
        },
    )
    assert response.status_code == 409
    assert "A candidate with this email already exists." in response.json()["detail"]


async def test_create_candidate_duplicate_email_case_insensitive(client: AsyncClient):
    await client.post(
        "/api/candidates",
        json={
            "full_name": "Alice Johnson",
            "email": "alice@example.com",
        },
    )

    response = await client.post(
        "/api/candidates",
        json={
            "full_name": "Alice Smith",
            "email": "Alice@Example.COM",
        },
    )
    assert response.status_code == 409
    assert "A candidate with this email already exists." in response.json()["detail"]


async def test_list_candidates_with_data(client: AsyncClient):
    await client.post(
        "/api/candidates",
        json={
            "full_name": "Alice Johnson",
            "email": "alice@example.com",
        },
    )
    await client.post(
        "/api/candidates",
        json={
            "full_name": "Bob Smith",
            "email": "bob@example.com",
        },
    )

    response = await client.get("/api/candidates")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2
    assert len(data["items"]) == 2
    assert data["items"][0]["full_name"] in ["Alice Johnson", "Bob Smith"]
    assert data["items"][0]["positions"] == []


async def test_list_candidates_with_positions(
    client: AsyncClient, session: AsyncSession
):
    resp = await client.post(
        "/api/candidates",
        json={"full_name": "Alice", "email": "alice@example.com"},
    )
    candidate_id = resp.json()["id"]

    team = Team(name="Engineering")
    session.add(team)
    await session.commit()
    await session.refresh(team)

    user = User(email="hm@provectus.com", google_id="hm123", full_name="Hiring Manager")
    session.add(user)
    await session.commit()
    await session.refresh(user)

    position = Position(
        title="Backend Engineer",
        team_id=team.id,
        hiring_manager_id=user.id,
        status="open",
    )
    session.add(position)
    await session.commit()
    await session.refresh(position)

    cp = CandidatePosition(
        candidate_id=candidate_id, position_id=position.id, stage="new"
    )
    session.add(cp)
    await session.commit()

    response = await client.get("/api/candidates")
    assert response.status_code == 200
    items = response.json()["items"]
    assert len(items) == 1
    assert len(items[0]["positions"]) == 1
    assert items[0]["positions"][0]["position_title"] == "Backend Engineer"
    assert items[0]["positions"][0]["stage"] == "new"
    assert items[0]["positions"][0]["position_id"] == position.id


async def test_list_candidates_pagination(client: AsyncClient):
    await client.post(
        "/api/candidates",
        json={"full_name": "Alice", "email": "alice@example.com"},
    )
    await client.post(
        "/api/candidates",
        json={"full_name": "Bob", "email": "bob@example.com"},
    )
    await client.post(
        "/api/candidates",
        json={"full_name": "Charlie", "email": "charlie@example.com"},
    )

    response = await client.get("/api/candidates?limit=2")
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 2
    assert data["total"] == 3
    assert data["limit"] == 2
    assert data["offset"] == 0


async def test_get_candidate_detail(client: AsyncClient):
    resp = await client.post(
        "/api/candidates",
        json={"full_name": "Alice Johnson", "email": "alice@example.com"},
    )
    candidate_id = resp.json()["id"]

    response = await client.get(f"/api/candidates/{candidate_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == candidate_id
    assert data["full_name"] == "Alice Johnson"
    assert data["email"] == "alice@example.com"
    assert data["is_archived"] is False
    assert data["positions"] == []
    assert "created_at" in data
    assert "updated_at" in data


async def test_get_candidate_not_found(client: AsyncClient):
    response = await client.get("/api/candidates/99999")
    assert response.status_code == 404
    assert "Candidate not found" in response.json()["detail"]


async def test_get_candidate_detail_with_positions(
    client: AsyncClient, session: AsyncSession
):
    resp = await client.post(
        "/api/candidates",
        json={"full_name": "Alice", "email": "alice@example.com"},
    )
    candidate_id = resp.json()["id"]

    team = Team(name="Engineering")
    session.add(team)
    await session.commit()
    await session.refresh(team)

    user = User(email="hm@provectus.com", google_id="hm123", full_name="Hiring Manager")
    session.add(user)
    await session.commit()
    await session.refresh(user)

    position = Position(
        title="Backend Engineer",
        team_id=team.id,
        hiring_manager_id=user.id,
        status="open",
    )
    session.add(position)
    await session.commit()
    await session.refresh(position)

    cp = CandidatePosition(
        candidate_id=candidate_id, position_id=position.id, stage="interview"
    )
    session.add(cp)
    await session.commit()

    response = await client.get(f"/api/candidates/{candidate_id}")
    assert response.status_code == 200
    data = response.json()
    assert len(data["positions"]) == 1
    assert data["positions"][0]["position_id"] == position.id
    assert data["positions"][0]["position_title"] == "Backend Engineer"
    assert data["positions"][0]["stage"] == "interview"


async def test_update_candidate_name(client: AsyncClient):
    resp = await client.post(
        "/api/candidates",
        json={"full_name": "Alice Johnson", "email": "alice@example.com"},
    )
    candidate_id = resp.json()["id"]

    response = await client.patch(
        f"/api/candidates/{candidate_id}",
        json={"full_name": "Alice Smith"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["full_name"] == "Alice Smith"
    assert data["email"] == "alice@example.com"


async def test_update_candidate_email(client: AsyncClient):
    resp = await client.post(
        "/api/candidates",
        json={"full_name": "Alice Johnson", "email": "alice@example.com"},
    )
    candidate_id = resp.json()["id"]

    response = await client.patch(
        f"/api/candidates/{candidate_id}",
        json={"email": "alice.new@example.com"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "alice.new@example.com"
    assert data["full_name"] == "Alice Johnson"


async def test_update_candidate_email_conflict(client: AsyncClient):
    resp1 = await client.post(
        "/api/candidates",
        json={"full_name": "Alice", "email": "alice@example.com"},
    )
    candidate_id1 = resp1.json()["id"]

    await client.post(
        "/api/candidates",
        json={"full_name": "Bob", "email": "bob@example.com"},
    )

    response = await client.patch(
        f"/api/candidates/{candidate_id1}",
        json={"email": "bob@example.com"},
    )
    assert response.status_code == 409
    assert "A candidate with this email already exists." in response.json()["detail"]


async def test_update_candidate_not_found(client: AsyncClient):
    response = await client.patch(
        "/api/candidates/99999",
        json={"full_name": "New Name"},
    )
    assert response.status_code == 404
    assert "Candidate not found" in response.json()["detail"]


async def test_add_candidate_to_position(client: AsyncClient, session: AsyncSession):
    resp = await client.post(
        "/api/candidates",
        json={"full_name": "Alice", "email": "alice@example.com"},
    )
    candidate_id = resp.json()["id"]

    team = Team(name="Engineering")
    session.add(team)
    await session.commit()
    await session.refresh(team)

    user = User(email="hm@provectus.com", google_id="hm123", full_name="Hiring Manager")
    session.add(user)
    await session.commit()
    await session.refresh(user)

    position = Position(
        title="Backend Engineer",
        team_id=team.id,
        hiring_manager_id=user.id,
        status="open",
    )
    session.add(position)
    await session.commit()
    await session.refresh(position)

    response = await client.post(
        f"/api/candidates/{candidate_id}/positions",
        json={"position_id": position.id},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["candidate_id"] == candidate_id
    assert data["position_id"] == position.id
    assert data["stage"] == "new"
    assert "id" in data
    assert "created_at" in data
    assert "updated_at" in data


async def test_add_candidate_to_position_duplicate(
    client: AsyncClient, session: AsyncSession
):
    resp = await client.post(
        "/api/candidates",
        json={"full_name": "Alice", "email": "alice@example.com"},
    )
    candidate_id = resp.json()["id"]

    team = Team(name="Engineering")
    session.add(team)
    await session.commit()
    await session.refresh(team)

    user = User(email="hm@provectus.com", google_id="hm123", full_name="Hiring Manager")
    session.add(user)
    await session.commit()
    await session.refresh(user)

    position = Position(
        title="Backend Engineer",
        team_id=team.id,
        hiring_manager_id=user.id,
        status="open",
    )
    session.add(position)
    await session.commit()
    await session.refresh(position)

    await client.post(
        f"/api/candidates/{candidate_id}/positions",
        json={"position_id": position.id},
    )

    response = await client.post(
        f"/api/candidates/{candidate_id}/positions",
        json={"position_id": position.id},
    )
    assert response.status_code == 409
    assert "already associated" in response.json()["detail"].lower()


async def test_add_candidate_to_position_not_found(
    client: AsyncClient, session: AsyncSession
):
    team = Team(name="Engineering")
    session.add(team)
    await session.commit()
    await session.refresh(team)

    user = User(email="hm@provectus.com", google_id="hm123", full_name="Hiring Manager")
    session.add(user)
    await session.commit()
    await session.refresh(user)

    position = Position(
        title="Backend Engineer",
        team_id=team.id,
        hiring_manager_id=user.id,
        status="open",
    )
    session.add(position)
    await session.commit()
    await session.refresh(position)

    response = await client.post(
        "/api/candidates/99999/positions",
        json={"position_id": position.id},
    )
    assert response.status_code == 404
    assert "Candidate not found" in response.json()["detail"]


async def test_add_candidate_to_position_position_not_found(client: AsyncClient):
    resp = await client.post(
        "/api/candidates",
        json={"full_name": "Alice", "email": "alice@example.com"},
    )
    candidate_id = resp.json()["id"]

    response = await client.post(
        f"/api/candidates/{candidate_id}/positions",
        json={"position_id": 99999},
    )
    assert response.status_code == 404
    assert "Position not found" in response.json()["detail"]


async def test_remove_candidate_from_position(
    client: AsyncClient, session: AsyncSession
):
    resp = await client.post(
        "/api/candidates",
        json={"full_name": "Alice", "email": "alice@example.com"},
    )
    candidate_id = resp.json()["id"]

    team = Team(name="Engineering")
    session.add(team)
    await session.commit()
    await session.refresh(team)

    user = User(email="hm@provectus.com", google_id="hm123", full_name="Hiring Manager")
    session.add(user)
    await session.commit()
    await session.refresh(user)

    position = Position(
        title="Backend Engineer",
        team_id=team.id,
        hiring_manager_id=user.id,
        status="open",
    )
    session.add(position)
    await session.commit()
    await session.refresh(position)

    await client.post(
        f"/api/candidates/{candidate_id}/positions",
        json={"position_id": position.id},
    )

    response = await client.delete(
        f"/api/candidates/{candidate_id}/positions/{position.id}"
    )
    assert response.status_code == 204


async def test_remove_candidate_from_position_not_found(client: AsyncClient):
    resp = await client.post(
        "/api/candidates",
        json={"full_name": "Alice", "email": "alice@example.com"},
    )
    candidate_id = resp.json()["id"]

    response = await client.delete(f"/api/candidates/{candidate_id}/positions/99999")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


async def advance_to_stage(
    client: AsyncClient, candidate_id: int, position_id: int, target_stage: str
):
    """Advance a candidate-position link to target stage through all required
    stages."""
    stage_order = ["new", "screening", "technical", "offer", "hired"]
    current_idx = 0
    target_idx = stage_order.index(target_stage)
    for i in range(current_idx + 1, target_idx + 1):
        resp = await client.patch(
            f"/api/candidates/{candidate_id}/positions/{position_id}",
            json={"stage": stage_order[i]},
        )
        assert resp.status_code == 200


async def test_stage_transition_new_to_screening(
    client: AsyncClient, session: AsyncSession
):
    resp = await client.post(
        "/api/candidates",
        json={"full_name": "Alice", "email": "alice@example.com"},
    )
    candidate_id = resp.json()["id"]

    team = Team(name="Engineering")
    session.add(team)
    await session.commit()
    await session.refresh(team)

    user = User(email="hm@provectus.com", google_id="hm123", full_name="Hiring Manager")
    session.add(user)
    await session.commit()
    await session.refresh(user)

    position = Position(
        title="Backend Engineer",
        team_id=team.id,
        hiring_manager_id=user.id,
        status="open",
    )
    session.add(position)
    await session.commit()
    await session.refresh(position)

    await client.post(
        f"/api/candidates/{candidate_id}/positions",
        json={"position_id": position.id},
    )

    response = await client.patch(
        f"/api/candidates/{candidate_id}/positions/{position.id}",
        json={"stage": "screening"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["stage"] == "screening"
    assert data["candidate_id"] == candidate_id
    assert data["position_id"] == position.id


async def test_stage_transition_screening_to_technical(
    client: AsyncClient, session: AsyncSession
):
    resp = await client.post(
        "/api/candidates",
        json={"full_name": "Alice", "email": "alice@example.com"},
    )
    candidate_id = resp.json()["id"]

    team = Team(name="Engineering")
    session.add(team)
    await session.commit()
    await session.refresh(team)

    user = User(email="hm@provectus.com", google_id="hm123", full_name="Hiring Manager")
    session.add(user)
    await session.commit()
    await session.refresh(user)

    position = Position(
        title="Backend Engineer",
        team_id=team.id,
        hiring_manager_id=user.id,
        status="open",
    )
    session.add(position)
    await session.commit()
    await session.refresh(position)

    await client.post(
        f"/api/candidates/{candidate_id}/positions",
        json={"position_id": position.id},
    )

    await advance_to_stage(client, candidate_id, position.id, "screening")

    response = await client.patch(
        f"/api/candidates/{candidate_id}/positions/{position.id}",
        json={"stage": "technical"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["stage"] == "technical"


async def test_stage_transition_technical_to_offer(
    client: AsyncClient, session: AsyncSession
):
    resp = await client.post(
        "/api/candidates",
        json={"full_name": "Alice", "email": "alice@example.com"},
    )
    candidate_id = resp.json()["id"]

    team = Team(name="Engineering")
    session.add(team)
    await session.commit()
    await session.refresh(team)

    user = User(email="hm@provectus.com", google_id="hm123", full_name="Hiring Manager")
    session.add(user)
    await session.commit()
    await session.refresh(user)

    position = Position(
        title="Backend Engineer",
        team_id=team.id,
        hiring_manager_id=user.id,
        status="open",
    )
    session.add(position)
    await session.commit()
    await session.refresh(position)

    await client.post(
        f"/api/candidates/{candidate_id}/positions",
        json={"position_id": position.id},
    )

    await advance_to_stage(client, candidate_id, position.id, "technical")

    response = await client.patch(
        f"/api/candidates/{candidate_id}/positions/{position.id}",
        json={"stage": "offer"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["stage"] == "offer"


async def test_stage_transition_offer_to_hired(
    client: AsyncClient, session: AsyncSession
):
    resp = await client.post(
        "/api/candidates",
        json={"full_name": "Alice", "email": "alice@example.com"},
    )
    candidate_id = resp.json()["id"]

    team = Team(name="Engineering")
    session.add(team)
    await session.commit()
    await session.refresh(team)

    user = User(email="hm@provectus.com", google_id="hm123", full_name="Hiring Manager")
    session.add(user)
    await session.commit()
    await session.refresh(user)

    position = Position(
        title="Backend Engineer",
        team_id=team.id,
        hiring_manager_id=user.id,
        status="open",
    )
    session.add(position)
    await session.commit()
    await session.refresh(position)

    await client.post(
        f"/api/candidates/{candidate_id}/positions",
        json={"position_id": position.id},
    )

    await advance_to_stage(client, candidate_id, position.id, "offer")

    response = await client.patch(
        f"/api/candidates/{candidate_id}/positions/{position.id}",
        json={"stage": "hired"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["stage"] == "hired"


async def test_stage_transition_new_to_rejected(
    client: AsyncClient, session: AsyncSession
):
    resp = await client.post(
        "/api/candidates",
        json={"full_name": "Alice", "email": "alice@example.com"},
    )
    candidate_id = resp.json()["id"]

    team = Team(name="Engineering")
    session.add(team)
    await session.commit()
    await session.refresh(team)

    user = User(email="hm@provectus.com", google_id="hm123", full_name="Hiring Manager")
    session.add(user)
    await session.commit()
    await session.refresh(user)

    position = Position(
        title="Backend Engineer",
        team_id=team.id,
        hiring_manager_id=user.id,
        status="open",
    )
    session.add(position)
    await session.commit()
    await session.refresh(position)

    await client.post(
        f"/api/candidates/{candidate_id}/positions",
        json={"position_id": position.id},
    )

    response = await client.patch(
        f"/api/candidates/{candidate_id}/positions/{position.id}",
        json={"stage": "rejected"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["stage"] == "rejected"


async def test_stage_transition_screening_to_rejected(
    client: AsyncClient, session: AsyncSession
):
    resp = await client.post(
        "/api/candidates",
        json={"full_name": "Alice", "email": "alice@example.com"},
    )
    candidate_id = resp.json()["id"]

    team = Team(name="Engineering")
    session.add(team)
    await session.commit()
    await session.refresh(team)

    user = User(email="hm@provectus.com", google_id="hm123", full_name="Hiring Manager")
    session.add(user)
    await session.commit()
    await session.refresh(user)

    position = Position(
        title="Backend Engineer",
        team_id=team.id,
        hiring_manager_id=user.id,
        status="open",
    )
    session.add(position)
    await session.commit()
    await session.refresh(position)

    await client.post(
        f"/api/candidates/{candidate_id}/positions",
        json={"position_id": position.id},
    )

    await advance_to_stage(client, candidate_id, position.id, "screening")

    response = await client.patch(
        f"/api/candidates/{candidate_id}/positions/{position.id}",
        json={"stage": "rejected"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["stage"] == "rejected"


async def test_stage_transition_technical_to_rejected(
    client: AsyncClient, session: AsyncSession
):
    resp = await client.post(
        "/api/candidates",
        json={"full_name": "Alice", "email": "alice@example.com"},
    )
    candidate_id = resp.json()["id"]

    team = Team(name="Engineering")
    session.add(team)
    await session.commit()
    await session.refresh(team)

    user = User(email="hm@provectus.com", google_id="hm123", full_name="Hiring Manager")
    session.add(user)
    await session.commit()
    await session.refresh(user)

    position = Position(
        title="Backend Engineer",
        team_id=team.id,
        hiring_manager_id=user.id,
        status="open",
    )
    session.add(position)
    await session.commit()
    await session.refresh(position)

    await client.post(
        f"/api/candidates/{candidate_id}/positions",
        json={"position_id": position.id},
    )

    await advance_to_stage(client, candidate_id, position.id, "technical")

    response = await client.patch(
        f"/api/candidates/{candidate_id}/positions/{position.id}",
        json={"stage": "rejected"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["stage"] == "rejected"


async def test_stage_transition_offer_to_rejected(
    client: AsyncClient, session: AsyncSession
):
    resp = await client.post(
        "/api/candidates",
        json={"full_name": "Alice", "email": "alice@example.com"},
    )
    candidate_id = resp.json()["id"]

    team = Team(name="Engineering")
    session.add(team)
    await session.commit()
    await session.refresh(team)

    user = User(email="hm@provectus.com", google_id="hm123", full_name="Hiring Manager")
    session.add(user)
    await session.commit()
    await session.refresh(user)

    position = Position(
        title="Backend Engineer",
        team_id=team.id,
        hiring_manager_id=user.id,
        status="open",
    )
    session.add(position)
    await session.commit()
    await session.refresh(position)

    await client.post(
        f"/api/candidates/{candidate_id}/positions",
        json={"position_id": position.id},
    )

    await advance_to_stage(client, candidate_id, position.id, "offer")

    response = await client.patch(
        f"/api/candidates/{candidate_id}/positions/{position.id}",
        json={"stage": "rejected"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["stage"] == "rejected"


async def test_stage_transition_screening_to_new_invalid(
    client: AsyncClient, session: AsyncSession
):
    resp = await client.post(
        "/api/candidates",
        json={"full_name": "Alice", "email": "alice@example.com"},
    )
    candidate_id = resp.json()["id"]

    team = Team(name="Engineering")
    session.add(team)
    await session.commit()
    await session.refresh(team)

    user = User(email="hm@provectus.com", google_id="hm123", full_name="Hiring Manager")
    session.add(user)
    await session.commit()
    await session.refresh(user)

    position = Position(
        title="Backend Engineer",
        team_id=team.id,
        hiring_manager_id=user.id,
        status="open",
    )
    session.add(position)
    await session.commit()
    await session.refresh(position)

    await client.post(
        f"/api/candidates/{candidate_id}/positions",
        json={"position_id": position.id},
    )

    await advance_to_stage(client, candidate_id, position.id, "screening")

    response = await client.patch(
        f"/api/candidates/{candidate_id}/positions/{position.id}", json={"stage": "new"}
    )
    assert response.status_code == 422
    assert "Invalid stage transition" in response.json()["detail"]


async def test_stage_transition_technical_to_screening_invalid(
    client: AsyncClient, session: AsyncSession
):
    resp = await client.post(
        "/api/candidates",
        json={"full_name": "Alice", "email": "alice@example.com"},
    )
    candidate_id = resp.json()["id"]

    team = Team(name="Engineering")
    session.add(team)
    await session.commit()
    await session.refresh(team)

    user = User(email="hm@provectus.com", google_id="hm123", full_name="Hiring Manager")
    session.add(user)
    await session.commit()
    await session.refresh(user)

    position = Position(
        title="Backend Engineer",
        team_id=team.id,
        hiring_manager_id=user.id,
        status="open",
    )
    session.add(position)
    await session.commit()
    await session.refresh(position)

    await client.post(
        f"/api/candidates/{candidate_id}/positions",
        json={"position_id": position.id},
    )

    await advance_to_stage(client, candidate_id, position.id, "technical")

    response = await client.patch(
        f"/api/candidates/{candidate_id}/positions/{position.id}",
        json={"stage": "screening"},
    )
    assert response.status_code == 422
    assert "Invalid stage transition" in response.json()["detail"]


async def test_stage_transition_offer_to_technical_invalid(
    client: AsyncClient, session: AsyncSession
):
    resp = await client.post(
        "/api/candidates",
        json={"full_name": "Alice", "email": "alice@example.com"},
    )
    candidate_id = resp.json()["id"]

    team = Team(name="Engineering")
    session.add(team)
    await session.commit()
    await session.refresh(team)

    user = User(email="hm@provectus.com", google_id="hm123", full_name="Hiring Manager")
    session.add(user)
    await session.commit()
    await session.refresh(user)

    position = Position(
        title="Backend Engineer",
        team_id=team.id,
        hiring_manager_id=user.id,
        status="open",
    )
    session.add(position)
    await session.commit()
    await session.refresh(position)

    await client.post(
        f"/api/candidates/{candidate_id}/positions",
        json={"position_id": position.id},
    )

    await advance_to_stage(client, candidate_id, position.id, "offer")

    response = await client.patch(
        f"/api/candidates/{candidate_id}/positions/{position.id}",
        json={"stage": "technical"},
    )
    assert response.status_code == 422
    assert "Invalid stage transition" in response.json()["detail"]


async def test_stage_transition_new_to_technical_invalid(
    client: AsyncClient, session: AsyncSession
):
    resp = await client.post(
        "/api/candidates",
        json={"full_name": "Alice", "email": "alice@example.com"},
    )
    candidate_id = resp.json()["id"]

    team = Team(name="Engineering")
    session.add(team)
    await session.commit()
    await session.refresh(team)

    user = User(email="hm@provectus.com", google_id="hm123", full_name="Hiring Manager")
    session.add(user)
    await session.commit()
    await session.refresh(user)

    position = Position(
        title="Backend Engineer",
        team_id=team.id,
        hiring_manager_id=user.id,
        status="open",
    )
    session.add(position)
    await session.commit()
    await session.refresh(position)

    await client.post(
        f"/api/candidates/{candidate_id}/positions",
        json={"position_id": position.id},
    )

    response = await client.patch(
        f"/api/candidates/{candidate_id}/positions/{position.id}",
        json={"stage": "technical"},
    )
    assert response.status_code == 422
    assert "Invalid stage transition" in response.json()["detail"]


async def test_stage_transition_new_to_offer_invalid(
    client: AsyncClient, session: AsyncSession
):
    resp = await client.post(
        "/api/candidates",
        json={"full_name": "Alice", "email": "alice@example.com"},
    )
    candidate_id = resp.json()["id"]

    team = Team(name="Engineering")
    session.add(team)
    await session.commit()
    await session.refresh(team)

    user = User(email="hm@provectus.com", google_id="hm123", full_name="Hiring Manager")
    session.add(user)
    await session.commit()
    await session.refresh(user)

    position = Position(
        title="Backend Engineer",
        team_id=team.id,
        hiring_manager_id=user.id,
        status="open",
    )
    session.add(position)
    await session.commit()
    await session.refresh(position)

    await client.post(
        f"/api/candidates/{candidate_id}/positions",
        json={"position_id": position.id},
    )

    response = await client.patch(
        f"/api/candidates/{candidate_id}/positions/{position.id}",
        json={"stage": "offer"},
    )
    assert response.status_code == 422
    assert "Invalid stage transition" in response.json()["detail"]


async def test_stage_transition_screening_to_offer_invalid(
    client: AsyncClient, session: AsyncSession
):
    resp = await client.post(
        "/api/candidates",
        json={"full_name": "Alice", "email": "alice@example.com"},
    )
    candidate_id = resp.json()["id"]

    team = Team(name="Engineering")
    session.add(team)
    await session.commit()
    await session.refresh(team)

    user = User(email="hm@provectus.com", google_id="hm123", full_name="Hiring Manager")
    session.add(user)
    await session.commit()
    await session.refresh(user)

    position = Position(
        title="Backend Engineer",
        team_id=team.id,
        hiring_manager_id=user.id,
        status="open",
    )
    session.add(position)
    await session.commit()
    await session.refresh(position)

    await client.post(
        f"/api/candidates/{candidate_id}/positions",
        json={"position_id": position.id},
    )

    await advance_to_stage(client, candidate_id, position.id, "screening")

    response = await client.patch(
        f"/api/candidates/{candidate_id}/positions/{position.id}",
        json={"stage": "offer"},
    )
    assert response.status_code == 422
    assert "Invalid stage transition" in response.json()["detail"]


async def test_stage_transition_hired_to_any_invalid(
    client: AsyncClient, session: AsyncSession
):
    resp = await client.post(
        "/api/candidates",
        json={"full_name": "Alice", "email": "alice@example.com"},
    )
    candidate_id = resp.json()["id"]

    team = Team(name="Engineering")
    session.add(team)
    await session.commit()
    await session.refresh(team)

    user = User(email="hm@provectus.com", google_id="hm123", full_name="Hiring Manager")
    session.add(user)
    await session.commit()
    await session.refresh(user)

    position = Position(
        title="Backend Engineer",
        team_id=team.id,
        hiring_manager_id=user.id,
        status="open",
    )
    session.add(position)
    await session.commit()
    await session.refresh(position)

    await client.post(
        f"/api/candidates/{candidate_id}/positions",
        json={"position_id": position.id},
    )

    await advance_to_stage(client, candidate_id, position.id, "hired")

    response = await client.patch(
        f"/api/candidates/{candidate_id}/positions/{position.id}",
        json={"stage": "screening"},
    )
    assert response.status_code == 422
    assert "Invalid stage transition" in response.json()["detail"]


async def test_stage_transition_rejected_to_any_invalid(
    client: AsyncClient, session: AsyncSession
):
    resp = await client.post(
        "/api/candidates",
        json={"full_name": "Alice", "email": "alice@example.com"},
    )
    candidate_id = resp.json()["id"]

    team = Team(name="Engineering")
    session.add(team)
    await session.commit()
    await session.refresh(team)

    user = User(email="hm@provectus.com", google_id="hm123", full_name="Hiring Manager")
    session.add(user)
    await session.commit()
    await session.refresh(user)

    position = Position(
        title="Backend Engineer",
        team_id=team.id,
        hiring_manager_id=user.id,
        status="open",
    )
    session.add(position)
    await session.commit()
    await session.refresh(position)

    await client.post(
        f"/api/candidates/{candidate_id}/positions",
        json={"position_id": position.id},
    )

    await advance_to_stage(client, candidate_id, position.id, "screening")

    await client.patch(
        f"/api/candidates/{candidate_id}/positions/{position.id}",
        json={"stage": "rejected"},
    )

    response = await client.patch(
        f"/api/candidates/{candidate_id}/positions/{position.id}",
        json={"stage": "screening"},
    )
    assert response.status_code == 422
    assert "Invalid stage transition" in response.json()["detail"]


async def test_stage_transition_invalid_stage_value(
    client: AsyncClient, session: AsyncSession
):
    resp = await client.post(
        "/api/candidates",
        json={"full_name": "Alice", "email": "alice@example.com"},
    )
    candidate_id = resp.json()["id"]

    team = Team(name="Engineering")
    session.add(team)
    await session.commit()
    await session.refresh(team)

    user = User(email="hm@provectus.com", google_id="hm123", full_name="Hiring Manager")
    session.add(user)
    await session.commit()
    await session.refresh(user)

    position = Position(
        title="Backend Engineer",
        team_id=team.id,
        hiring_manager_id=user.id,
        status="open",
    )
    session.add(position)
    await session.commit()
    await session.refresh(position)

    await client.post(
        f"/api/candidates/{candidate_id}/positions",
        json={"position_id": position.id},
    )

    response = await client.patch(
        f"/api/candidates/{candidate_id}/positions/{position.id}",
        json={"stage": "bogus"},
    )
    assert response.status_code == 422
    assert "Invalid stage" in response.json()["detail"]


async def test_update_stage_not_found(client: AsyncClient):
    resp = await client.post(
        "/api/candidates",
        json={"full_name": "Alice", "email": "alice@example.com"},
    )
    candidate_id = resp.json()["id"]

    response = await client.patch(
        f"/api/candidates/{candidate_id}/positions/99999", json={"stage": "screening"}
    )
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


async def test_search_candidates_by_name(client: AsyncClient):
    await client.post(
        "/api/candidates",
        json={"full_name": "Alice Johnson", "email": "alice@example.com"},
    )
    await client.post(
        "/api/candidates",
        json={"full_name": "Bob Smith", "email": "bob@example.com"},
    )

    response = await client.get("/api/candidates?search=alice")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert len(data["items"]) == 1
    assert data["items"][0]["full_name"] == "Alice Johnson"


async def test_search_candidates_by_email(client: AsyncClient):
    await client.post(
        "/api/candidates",
        json={"full_name": "Alice Johnson", "email": "alice@example.com"},
    )
    await client.post(
        "/api/candidates",
        json={"full_name": "Bob Smith", "email": "bob@example.com"},
    )

    response = await client.get("/api/candidates?search=bob@")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert len(data["items"]) == 1
    assert data["items"][0]["email"] == "bob@example.com"


async def test_search_candidates_case_insensitive(client: AsyncClient):
    await client.post(
        "/api/candidates",
        json={"full_name": "Alice Johnson", "email": "alice@example.com"},
    )

    response = await client.get("/api/candidates?search=ALICE")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["full_name"] == "Alice Johnson"


async def test_filter_candidates_by_stage(client: AsyncClient, session: AsyncSession):
    resp1 = await client.post(
        "/api/candidates",
        json={"full_name": "Alice", "email": "alice@example.com"},
    )
    candidate_id1 = resp1.json()["id"]

    resp2 = await client.post(
        "/api/candidates",
        json={"full_name": "Bob", "email": "bob@example.com"},
    )
    candidate_id2 = resp2.json()["id"]

    team = Team(name="Engineering")
    session.add(team)
    await session.commit()
    await session.refresh(team)

    user = User(email="hm@provectus.com", google_id="hm123", full_name="Hiring Manager")
    session.add(user)
    await session.commit()
    await session.refresh(user)

    position = Position(
        title="Backend Engineer",
        team_id=team.id,
        hiring_manager_id=user.id,
        status="open",
    )
    session.add(position)
    await session.commit()
    await session.refresh(position)

    cp1 = CandidatePosition(
        candidate_id=candidate_id1, position_id=position.id, stage="new"
    )
    session.add(cp1)

    cp2 = CandidatePosition(
        candidate_id=candidate_id2, position_id=position.id, stage="screening"
    )
    session.add(cp2)
    await session.commit()

    response = await client.get("/api/candidates?stage=screening")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert len(data["items"]) == 1
    assert data["items"][0]["full_name"] == "Bob"


async def test_filter_candidates_by_position(
    client: AsyncClient, session: AsyncSession
):
    resp1 = await client.post(
        "/api/candidates",
        json={"full_name": "Alice", "email": "alice@example.com"},
    )
    candidate_id1 = resp1.json()["id"]

    resp2 = await client.post(
        "/api/candidates",
        json={"full_name": "Bob", "email": "bob@example.com"},
    )
    candidate_id2 = resp2.json()["id"]

    team = Team(name="Engineering")
    session.add(team)
    await session.commit()
    await session.refresh(team)

    user = User(email="hm@provectus.com", google_id="hm123", full_name="Hiring Manager")
    session.add(user)
    await session.commit()
    await session.refresh(user)

    position1 = Position(
        title="Backend Engineer",
        team_id=team.id,
        hiring_manager_id=user.id,
        status="open",
    )
    session.add(position1)
    await session.commit()
    await session.refresh(position1)

    position2 = Position(
        title="Frontend Engineer",
        team_id=team.id,
        hiring_manager_id=user.id,
        status="open",
    )
    session.add(position2)
    await session.commit()
    await session.refresh(position2)

    cp1 = CandidatePosition(
        candidate_id=candidate_id1, position_id=position1.id, stage="new"
    )
    session.add(cp1)

    cp2 = CandidatePosition(
        candidate_id=candidate_id2, position_id=position2.id, stage="new"
    )
    session.add(cp2)
    await session.commit()

    response = await client.get(f"/api/candidates?position_id={position1.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert len(data["items"]) == 1
    assert data["items"][0]["full_name"] == "Alice"


async def test_combined_search_and_filter(
    client: AsyncClient, session: AsyncSession
):
    resp1 = await client.post(
        "/api/candidates",
        json={"full_name": "Alice Johnson", "email": "alice@example.com"},
    )
    candidate_id1 = resp1.json()["id"]

    resp2 = await client.post(
        "/api/candidates",
        json={"full_name": "Alice Smith", "email": "alice.smith@example.com"},
    )
    candidate_id2 = resp2.json()["id"]

    team = Team(name="Engineering")
    session.add(team)
    await session.commit()
    await session.refresh(team)

    user = User(email="hm@provectus.com", google_id="hm123", full_name="Hiring Manager")
    session.add(user)
    await session.commit()
    await session.refresh(user)

    position = Position(
        title="Backend Engineer",
        team_id=team.id,
        hiring_manager_id=user.id,
        status="open",
    )
    session.add(position)
    await session.commit()
    await session.refresh(position)

    cp1 = CandidatePosition(
        candidate_id=candidate_id1, position_id=position.id, stage="new"
    )
    session.add(cp1)

    cp2 = CandidatePosition(
        candidate_id=candidate_id2, position_id=position.id, stage="screening"
    )
    session.add(cp2)
    await session.commit()

    response = await client.get("/api/candidates?search=alice&stage=screening")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert len(data["items"]) == 1
    assert data["items"][0]["full_name"] == "Alice Smith"


async def test_sort_candidates_by_name_asc(client: AsyncClient):
    await client.post(
        "/api/candidates",
        json={"full_name": "Carol", "email": "carol@example.com"},
    )
    await client.post(
        "/api/candidates",
        json={"full_name": "Alice", "email": "alice@example.com"},
    )
    await client.post(
        "/api/candidates",
        json={"full_name": "Bob", "email": "bob@example.com"},
    )

    response = await client.get("/api/candidates?sort_by=full_name&sort_order=asc")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 3
    assert len(data["items"]) == 3
    assert data["items"][0]["full_name"] == "Alice"
    assert data["items"][1]["full_name"] == "Bob"
    assert data["items"][2]["full_name"] == "Carol"


async def test_sort_candidates_by_name_desc(client: AsyncClient):
    await client.post(
        "/api/candidates",
        json={"full_name": "Carol", "email": "carol@example.com"},
    )
    await client.post(
        "/api/candidates",
        json={"full_name": "Alice", "email": "alice@example.com"},
    )
    await client.post(
        "/api/candidates",
        json={"full_name": "Bob", "email": "bob@example.com"},
    )

    response = await client.get("/api/candidates?sort_by=full_name&sort_order=desc")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 3
    assert len(data["items"]) == 3
    assert data["items"][0]["full_name"] == "Carol"
    assert data["items"][1]["full_name"] == "Bob"
    assert data["items"][2]["full_name"] == "Alice"


async def test_search_no_results(client: AsyncClient):
    await client.post(
        "/api/candidates",
        json={"full_name": "Alice", "email": "alice@example.com"},
    )

    response = await client.get("/api/candidates?search=nonexistent")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 0
    assert len(data["items"]) == 0


async def test_archive_candidate(client: AsyncClient):
    resp = await client.post(
        "/api/candidates",
        json={"full_name": "Alice Johnson", "email": "alice@example.com"},
    )
    candidate_id = resp.json()["id"]

    response = await client.post(f"/api/candidates/{candidate_id}/archive")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == candidate_id
    assert data["full_name"] == "Alice Johnson"
    assert data["email"] == "alice@example.com"
    assert data["is_archived"] is True


async def test_archive_candidate_hidden_from_list(client: AsyncClient):
    resp = await client.post(
        "/api/candidates",
        json={"full_name": "Alice Johnson", "email": "alice@example.com"},
    )
    candidate_id = resp.json()["id"]

    await client.post(f"/api/candidates/{candidate_id}/archive")

    response = await client.get("/api/candidates")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 0
    assert len(data["items"]) == 0


async def test_archive_candidate_not_found(client: AsyncClient):
    response = await client.post("/api/candidates/99999/archive")
    assert response.status_code == 404
    assert "Candidate not found" in response.json()["detail"]
