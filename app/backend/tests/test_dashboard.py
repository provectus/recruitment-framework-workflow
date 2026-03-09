import pytest
from httpx import AsyncClient
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models.candidate import Candidate
from app.models.candidate_position import CandidatePosition
from app.models.position import Position
from app.models.team import Team


@pytest.mark.asyncio
async def test_dashboard_stats_empty(authenticated_client: AsyncClient):
    response = await authenticated_client.get("/api/dashboard/stats")
    assert response.status_code == 200
    data = response.json()
    assert data["total_candidates"] == 0
    assert data["total_positions"] == 0
    assert data["open_positions"] == 0
    assert data["pipeline_counts"] == []
    assert data["recent_candidates"] == []
    assert data["positions_summary"] == []


@pytest.mark.asyncio
async def test_dashboard_stats_with_data(
    authenticated_client: AsyncClient,
    session: AsyncSession,
):
    team = Team(name="Engineering")
    session.add(team)
    await session.flush()

    position = Position(
        title="Backend Engineer",
        status="open",
        team_id=team.id,
        hiring_manager_id=1,
    )
    session.add(position)
    await session.flush()

    candidate = Candidate(
        full_name="Jane Doe",
        email="jane@example.com",
    )
    session.add(candidate)
    await session.flush()

    cp = CandidatePosition(
        candidate_id=candidate.id,
        position_id=position.id,
        stage="screening",
    )
    session.add(cp)
    await session.commit()

    response = await authenticated_client.get("/api/dashboard/stats")
    assert response.status_code == 200
    data = response.json()
    assert data["total_candidates"] == 1
    assert data["total_positions"] == 1
    assert data["open_positions"] == 1
    assert len(data["pipeline_counts"]) == 1
    assert data["pipeline_counts"][0]["stage"] == "screening"
    assert data["pipeline_counts"][0]["count"] == 1
    assert len(data["recent_candidates"]) == 1
    assert data["recent_candidates"][0]["full_name"] == "Jane Doe"
    assert len(data["positions_summary"]) == 1
    assert data["positions_summary"][0]["title"] == "Backend Engineer"
    assert data["positions_summary"][0]["candidate_count"] == 1


@pytest.mark.asyncio
async def test_dashboard_stats_requires_auth(client: AsyncClient):
    response = await client.get("/api/dashboard/stats")
    assert response.status_code == 401
