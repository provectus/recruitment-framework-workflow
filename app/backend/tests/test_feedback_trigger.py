from unittest.mock import AsyncMock, patch

import pytest
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models.candidate import Candidate
from app.models.candidate_position import CandidatePosition
from app.models.evaluation import Evaluation
from app.models.position import Position
from app.models.team import Team
from app.models.user import User
from app.services import evaluation_service

_PUBLISH_PATH = "app.services.eventbridge_service.publish_evaluation_event"


@pytest.fixture
async def hiring_manager(session: AsyncSession) -> User:
    user = User(
        email="manager@provectus.com",
        google_id="manager123",
        full_name="Hiring Manager",
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user


@pytest.fixture
async def candidate_position(
    session: AsyncSession, hiring_manager: User
) -> CandidatePosition:
    team = Team(name="Engineering")
    session.add(team)
    await session.flush()

    position = Position(
        title="Backend Engineer",
        team_id=team.id,
        hiring_manager_id=hiring_manager.id,
        status="open",
    )
    session.add(position)
    await session.flush()

    candidate = Candidate(full_name="Jane Applicant", email="jane@example.com")
    session.add(candidate)
    await session.flush()

    cp = CandidatePosition(
        candidate_id=candidate.id,
        position_id=position.id,
        stage="screening",
    )
    session.add(cp)
    await session.commit()
    await session.refresh(cp)
    return cp


@patch(_PUBLISH_PATH, new_callable=AsyncMock)
async def test_trigger_feedback_gen_creates_pending_evaluation(
    mock_publish: AsyncMock,
    session: AsyncSession,
    candidate_position: CandidatePosition,
) -> None:
    await evaluation_service.trigger_feedback_gen(
        session=session,
        candidate_position_id=candidate_position.id,
    )

    result = await session.exec(
        select(Evaluation).where(
            Evaluation.candidate_position_id == candidate_position.id,
            Evaluation.step_type == "feedback_gen",
        )
    )
    evaluations = list(result.all())

    assert len(evaluations) == 1
    assert evaluations[0].status == "pending"
    assert evaluations[0].step_type == "feedback_gen"
    assert evaluations[0].source_document_id is None
    assert evaluations[0].rubric_version_id is None


@patch(_PUBLISH_PATH, new_callable=AsyncMock)
async def test_trigger_feedback_gen_publishes_event(
    mock_publish: AsyncMock,
    session: AsyncSession,
    candidate_position: CandidatePosition,
) -> None:
    await evaluation_service.trigger_feedback_gen(
        session=session,
        candidate_position_id=candidate_position.id,
    )

    mock_publish.assert_called_once()
    call_kwargs = mock_publish.call_args.kwargs
    assert call_kwargs["step_type"] == "feedback_gen"
    assert call_kwargs["candidate_position_id"] == candidate_position.id


@patch(_PUBLISH_PATH, new_callable=AsyncMock)
async def test_rejecting_candidate_at_screening_creates_feedback_gen_evaluation(
    mock_publish: AsyncMock,
    session: AsyncSession,
    candidate_position: CandidatePosition,
) -> None:
    from app.services import candidate_service

    candidate = await session.get(Candidate, candidate_position.candidate_id)
    assert candidate is not None

    await candidate_service.update_stage(
        session=session,
        candidate_id=candidate.id,
        position_id=candidate_position.position_id,
        new_stage="rejected",
    )

    result = await session.exec(
        select(Evaluation).where(
            Evaluation.candidate_position_id == candidate_position.id,
            Evaluation.step_type == "feedback_gen",
        )
    )
    evaluations = list(result.all())

    assert len(evaluations) == 1
    assert evaluations[0].status == "pending"
    assert evaluations[0].step_type == "feedback_gen"


@patch(_PUBLISH_PATH, new_callable=AsyncMock)
async def test_rejecting_candidate_does_not_break_stage_transition(
    mock_publish: AsyncMock,
    session: AsyncSession,
    candidate_position: CandidatePosition,
) -> None:
    from app.services import candidate_service

    candidate = await session.get(Candidate, candidate_position.candidate_id)
    assert candidate is not None

    updated_cp = await candidate_service.update_stage(
        session=session,
        candidate_id=candidate.id,
        position_id=candidate_position.position_id,
        new_stage="rejected",
    )

    assert updated_cp.stage == "rejected"
    assert updated_cp.id == candidate_position.id


@patch(_PUBLISH_PATH, new_callable=AsyncMock)
async def test_non_rejection_stage_transition_does_not_trigger_feedback_gen(
    mock_publish: AsyncMock,
    session: AsyncSession,
    candidate_position: CandidatePosition,
) -> None:
    from app.services import candidate_service

    candidate = await session.get(Candidate, candidate_position.candidate_id)
    assert candidate is not None

    await candidate_service.update_stage(
        session=session,
        candidate_id=candidate.id,
        position_id=candidate_position.position_id,
        new_stage="technical",
    )

    result = await session.exec(
        select(Evaluation).where(
            Evaluation.candidate_position_id == candidate_position.id,
            Evaluation.step_type == "feedback_gen",
        )
    )
    evaluations = list(result.all())

    assert len(evaluations) == 0
