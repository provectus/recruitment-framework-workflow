"""Tests for the SSE evaluation status stream endpoint."""

import json
from contextlib import asynccontextmanager
from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models.candidate import Candidate
from app.models.candidate_position import CandidatePosition
from app.models.enums import EvaluationStatus, EvaluationStepType
from app.models.evaluation import Evaluation
from app.models.position import Position
from app.models.team import Team
from app.models.user import User


@pytest.fixture
async def candidate_position(session: AsyncSession) -> CandidatePosition:
    candidate = Candidate(full_name="Stream Tester", email="stream@example.com")
    session.add(candidate)
    await session.flush()

    team = Team(name="StreamTeam")
    session.add(team)
    await session.flush()

    user = User(
        email="hm@provectus.com",
        google_id="hm-sse-123",
        full_name="Hiring Manager SSE",
    )
    session.add(user)
    await session.flush()

    position = Position(
        title="SSE Engineer",
        team_id=team.id,
        hiring_manager_id=user.id,
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


def _parse_sse_events(raw: str) -> list[dict[str, str]]:
    """Parse SSE text into a list of event dicts with 'event' and 'data' keys."""
    events: list[dict[str, str]] = []
    current: dict[str, str] = {}

    for line in raw.splitlines():
        if line.startswith("event:"):
            current["event"] = line[len("event:") :].strip()
        elif line.startswith("data:"):
            current["data"] = line[len("data:") :].strip()
        elif line == "" and current:
            events.append(current)
            current = {}

    if current:
        events.append(current)

    return events


def make_session_factory_mock(session: AsyncSession):
    """Return a callable that acts as async_session_factory."""

    @asynccontextmanager
    async def _factory():
        yield session

    return _factory


class TestSSEContentType:
    async def test_returns_event_stream_content_type(
        self,
        authenticated_client: AsyncClient,
        candidate_position: CandidatePosition,
        session: AsyncSession,
    ) -> None:
        evaluation = Evaluation(
            candidate_position_id=candidate_position.id,
            step_type=EvaluationStepType.cv_analysis,
            status=EvaluationStatus.completed,
            version=1,
        )
        session.add(evaluation)
        await session.commit()

        with (
            patch(
                "app.routers.evaluations.async_session_factory",
                make_session_factory_mock(session),
            ),
            patch("app.routers.evaluations.asyncio.sleep", new_callable=AsyncMock),
        ):
            async with authenticated_client.stream(
                "GET",
                f"/api/evaluations/{candidate_position.id}/stream",
            ) as response:
                assert response.status_code == 200
                assert response.headers["content-type"].startswith("text/event-stream")
                await response.aread()


class TestSSENoEvaluations:
    async def test_no_done_event_emitted_with_no_prior_state(
        self,
        authenticated_client: AsyncClient,
        candidate_position: CandidatePosition,
    ) -> None:
        call_count = 0

        async def get_evaluations_returning_none_then_terminal(  # type: ignore[no-untyped-def]
            session, candidate_position_id
        ):
            nonlocal call_count
            call_count += 1
            if call_count >= 2:
                terminal = Evaluation(
                    id=99,
                    candidate_position_id=candidate_position_id,
                    step_type=EvaluationStepType.cv_analysis,
                    status=EvaluationStatus.completed,
                    version=1,
                )
                return [terminal]
            return []

        @asynccontextmanager
        async def fake_session_factory():
            yield AsyncMock()

        with (
            patch(
                "app.routers.evaluations.async_session_factory",
                fake_session_factory,
            ),
            patch(
                "app.routers.evaluations.evaluation_service.get_evaluations",
                get_evaluations_returning_none_then_terminal,
            ),
            patch("app.routers.evaluations.asyncio.sleep", new_callable=AsyncMock),
        ):
            async with authenticated_client.stream(
                "GET",
                f"/api/evaluations/{candidate_position.id}/stream",
            ) as response:
                assert response.status_code == 200
                body = (await response.aread()).decode()

        events = _parse_sse_events(body)
        event_names = [e.get("event") for e in events]
        assert "done" in event_names
        status_change_events = [e for e in events if e.get("event") == "status_change"]
        assert len(status_change_events) == 1


class TestSSEStatusChange:
    async def test_status_change_event_emitted_for_evaluation(
        self,
        authenticated_client: AsyncClient,
        candidate_position: CandidatePosition,
        session: AsyncSession,
    ) -> None:
        evaluation = Evaluation(
            candidate_position_id=candidate_position.id,
            step_type=EvaluationStepType.cv_analysis,
            status=EvaluationStatus.completed,
            version=1,
        )
        session.add(evaluation)
        await session.commit()
        await session.refresh(evaluation)

        with (
            patch(
                "app.routers.evaluations.async_session_factory",
                make_session_factory_mock(session),
            ),
            patch("app.routers.evaluations.asyncio.sleep", new_callable=AsyncMock),
        ):
            async with authenticated_client.stream(
                "GET",
                f"/api/evaluations/{candidate_position.id}/stream",
            ) as response:
                assert response.status_code == 200
                body = (await response.aread()).decode()

        events = _parse_sse_events(body)
        status_change_events = [e for e in events if e.get("event") == "status_change"]
        assert len(status_change_events) >= 1

        first_event_data = json.loads(status_change_events[0]["data"])
        assert first_event_data["evaluation_id"] == evaluation.id
        assert first_event_data["step_type"] == EvaluationStepType.cv_analysis
        assert first_event_data["status"] == EvaluationStatus.completed


class TestSSETerminalState:
    async def test_done_event_sent_when_all_evaluations_are_terminal(
        self,
        authenticated_client: AsyncClient,
        candidate_position: CandidatePosition,
        session: AsyncSession,
    ) -> None:
        for step_type, status in [
            (EvaluationStepType.cv_analysis, EvaluationStatus.completed),
            (EvaluationStepType.screening_eval, EvaluationStatus.failed),
        ]:
            evaluation = Evaluation(
                candidate_position_id=candidate_position.id,
                step_type=step_type,
                status=status,
                version=1,
            )
            session.add(evaluation)
        await session.commit()

        with (
            patch(
                "app.routers.evaluations.async_session_factory",
                make_session_factory_mock(session),
            ),
            patch("app.routers.evaluations.asyncio.sleep", new_callable=AsyncMock),
        ):
            async with authenticated_client.stream(
                "GET",
                f"/api/evaluations/{candidate_position.id}/stream",
            ) as response:
                assert response.status_code == 200
                body = (await response.aread()).decode()

        events = _parse_sse_events(body)
        event_names = [e.get("event") for e in events]
        assert "done" in event_names

    async def test_requires_authentication(
        self,
        client: AsyncClient,
        candidate_position: CandidatePosition,
    ) -> None:
        response = await client.get(f"/api/evaluations/{candidate_position.id}/stream")
        assert response.status_code == 401
