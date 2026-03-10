from datetime import date
from unittest.mock import AsyncMock, patch

import pytest
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models.candidate import Candidate
from app.models.candidate_position import CandidatePosition
from app.models.evaluation import Evaluation
from app.models.position import Position
from app.models.position_rubric import PositionRubric, PositionRubricVersion
from app.models.team import Team
from app.models.user import User
from app.services import document_service

_PUBLISH_PATH = "app.services.eventbridge_service.publish_evaluation_event"
_UPLOAD_URL_PATH = "app.services.storage_service.generate_upload_url"
_OBJECT_SIZE_PATH = "app.services.storage_service.get_object_size"
_PUT_TEXT_PATH = "app.services.storage_service.put_text_object"


@pytest.fixture
async def test_user(session: AsyncSession) -> User:
    user = User(
        email="uploader@provectus.com",
        google_id="uploader123",
        full_name="Uploader User",
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user


@pytest.fixture
async def interviewer(session: AsyncSession) -> User:
    user = User(
        email="interviewer@provectus.com",
        google_id="interviewer123",
        full_name="Jane Interviewer",
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user


@pytest.fixture
async def candidate_position(
    session: AsyncSession, test_user: User
) -> CandidatePosition:
    candidate = Candidate(full_name="Bob Candidate", email="bob@example.com")
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


@pytest.fixture
async def candidate_position_with_rubric(
    session: AsyncSession, candidate_position: CandidatePosition, test_user: User
) -> tuple[CandidatePosition, PositionRubricVersion]:
    rubric = PositionRubric(position_id=candidate_position.position_id)
    session.add(rubric)
    await session.flush()

    version = PositionRubricVersion(
        position_rubric_id=rubric.id,
        version_number=1,
        structure={"categories": []},
        created_by_id=test_user.id,
    )
    session.add(version)
    await session.commit()
    await session.refresh(version)
    return candidate_position, version


@patch(_PUBLISH_PATH, new_callable=AsyncMock)
@patch(_OBJECT_SIZE_PATH, new_callable=AsyncMock, return_value=0)
@patch(_UPLOAD_URL_PATH, new_callable=AsyncMock)
async def test_complete_cv_upload_creates_cv_analysis_evaluation(
    mock_upload_url: AsyncMock,
    mock_object_size: AsyncMock,
    mock_publish: AsyncMock,
    session: AsyncSession,
    candidate_position: CandidatePosition,
    test_user: User,
) -> None:
    mock_upload_url.return_value = "https://s3.example.com/upload"

    document, _ = await document_service.create_presigned_upload(
        session=session,
        type="cv",
        candidate_position_id=candidate_position.id,
        file_name="resume.pdf",
        content_type="application/pdf",
        file_size=1024,
        uploaded_by_id=test_user.id,
    )

    await document_service.complete_upload(
        session=session,
        document_id=document.id,
        user_id=test_user.id,
    )

    result = await session.exec(
        select(Evaluation).where(
            Evaluation.candidate_position_id == candidate_position.id
        )
    )
    evaluations = list(result.all())

    assert len(evaluations) == 1
    assert evaluations[0].step_type == "cv_analysis"
    assert evaluations[0].status == "pending"
    assert evaluations[0].source_document_id == document.id


@patch(_PUBLISH_PATH, new_callable=AsyncMock)
@patch(_OBJECT_SIZE_PATH, new_callable=AsyncMock, return_value=0)
@patch(_UPLOAD_URL_PATH, new_callable=AsyncMock)
async def test_complete_technical_transcript_without_rubric_skips_evaluation(
    mock_upload_url: AsyncMock,
    mock_object_size: AsyncMock,
    mock_publish: AsyncMock,
    session: AsyncSession,
    candidate_position: CandidatePosition,
    test_user: User,
    interviewer: User,
) -> None:
    mock_upload_url.return_value = "https://s3.example.com/upload"

    document, _ = await document_service.create_presigned_upload(
        session=session,
        type="transcript",
        candidate_position_id=candidate_position.id,
        file_name="interview.txt",
        content_type="text/plain",
        file_size=512,
        uploaded_by_id=test_user.id,
        interview_stage="technical",
        interviewer_id=interviewer.id,
        interview_date=date(2025, 1, 15),
    )

    await document_service.complete_upload(
        session=session,
        document_id=document.id,
        user_id=test_user.id,
    )

    result = await session.exec(
        select(Evaluation).where(
            Evaluation.candidate_position_id == candidate_position.id
        )
    )
    evaluations = list(result.all())

    assert len(evaluations) == 0
    mock_publish.assert_not_called()


@patch(_PUBLISH_PATH, new_callable=AsyncMock)
@patch(_PUT_TEXT_PATH, new_callable=AsyncMock)
async def test_paste_screening_transcript_creates_screening_eval(
    mock_put_text: AsyncMock,
    mock_publish: AsyncMock,
    session: AsyncSession,
    candidate_position: CandidatePosition,
    test_user: User,
    interviewer: User,
) -> None:
    await document_service.create_pasted_transcript(
        session=session,
        candidate_position_id=candidate_position.id,
        content="Transcript content here.",
        interview_stage="screening",
        interviewer_id=interviewer.id,
        interview_date=date(2025, 1, 15),
        uploaded_by_id=test_user.id,
    )

    result = await session.exec(
        select(Evaluation).where(
            Evaluation.candidate_position_id == candidate_position.id
        )
    )
    evaluations = list(result.all())

    assert len(evaluations) == 1
    assert evaluations[0].step_type == "screening_eval"
    assert evaluations[0].status == "pending"


@patch(_PUBLISH_PATH, new_callable=AsyncMock)
@patch(_OBJECT_SIZE_PATH, new_callable=AsyncMock, return_value=0)
@patch(_UPLOAD_URL_PATH, new_callable=AsyncMock)
async def test_eventbridge_skipped_when_bus_name_empty(
    mock_upload_url: AsyncMock,
    mock_object_size: AsyncMock,
    mock_publish: AsyncMock,
    session: AsyncSession,
    candidate_position: CandidatePosition,
    test_user: User,
) -> None:
    from app.config import settings
    from app.services import eventbridge_service

    mock_upload_url.return_value = "https://s3.example.com/upload"

    document, _ = await document_service.create_presigned_upload(
        session=session,
        type="cv",
        candidate_position_id=candidate_position.id,
        file_name="resume.pdf",
        content_type="application/pdf",
        file_size=1024,
        uploaded_by_id=test_user.id,
    )

    await document_service.complete_upload(
        session=session,
        document_id=document.id,
        user_id=test_user.id,
    )

    assert settings.evaluation_event_bus_name == ""
    mock_publish.assert_called_once()

    import aioboto3

    with (
        patch.object(settings, "evaluation_event_bus_name", ""),
        patch.object(aioboto3, "Session") as mock_session_cls,
    ):
        await eventbridge_service.publish_evaluation_event(
            evaluation_id=1,
            candidate_position_id=candidate_position.id,
            step_type="cv_analysis",
        )
        mock_session_cls.assert_not_called()
