from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient
from sqlmodel.ext.asyncio.session import AsyncSession

from app.exceptions import NotFoundException
from app.models.candidate import Candidate
from app.models.candidate_position import CandidatePosition
from app.models.enums import EvaluationStatus, EvaluationStepType
from app.models.evaluation import Evaluation
from app.models.position import Position
from app.models.team import Team
from app.models.user import User
from app.services import evaluation_service

_PUBLISH_PATH = "app.services.eventbridge_service.publish_evaluation_event"


@pytest.fixture
async def candidate_position(session: AsyncSession) -> CandidatePosition:
    candidate = Candidate(full_name="Carol Rerun", email="carol@example.com")
    session.add(candidate)
    await session.flush()

    team = Team(name="Platform")
    session.add(team)
    await session.flush()

    user = User(
        email="hm-rerun@provectus.com",
        google_id="hm-rerun-001",
        full_name="Hiring Manager Rerun",
    )
    session.add(user)
    await session.flush()

    position = Position(
        title="Platform Engineer",
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


async def _seed_evaluation(
    session: AsyncSession,
    candidate_position_id: int,
    step_type: EvaluationStepType,
    status: EvaluationStatus = EvaluationStatus.completed,
    source_document_id: int | None = 10,
    rubric_version_id: int | None = 5,
) -> Evaluation:
    evaluation = await evaluation_service.create_evaluation(
        session=session,
        candidate_position_id=candidate_position_id,
        step_type=step_type,
        source_document_id=source_document_id,
        rubric_version_id=rubric_version_id,
    )
    evaluation.status = status
    session.add(evaluation)
    await session.commit()
    await session.refresh(evaluation)
    return evaluation


class TestRerunEvaluation:
    @patch(_PUBLISH_PATH, new_callable=AsyncMock)
    async def test_rerun_creates_new_version_incrementing_from_latest(
        self,
        mock_publish: AsyncMock,
        session: AsyncSession,
        candidate_position: CandidatePosition,
    ) -> None:
        await _seed_evaluation(
            session,
            candidate_position.id,
            EvaluationStepType.cv_analysis,
        )

        result = await evaluation_service.rerun_evaluation(
            session=session,
            candidate_position_id=candidate_position.id,
            step_type=EvaluationStepType.cv_analysis,
        )

        assert len(result) == 1
        rerun = result[0]
        assert rerun.version == 2
        assert rerun.status == EvaluationStatus.pending
        assert rerun.step_type == EvaluationStepType.cv_analysis
        assert rerun.source_document_id == 10
        assert rerun.rubric_version_id == 5

    @patch(_PUBLISH_PATH, new_callable=AsyncMock)
    async def test_rerun_publishes_eventbridge_event(
        self,
        mock_publish: AsyncMock,
        session: AsyncSession,
        candidate_position: CandidatePosition,
    ) -> None:
        await _seed_evaluation(
            session,
            candidate_position.id,
            EvaluationStepType.cv_analysis,
        )

        result = await evaluation_service.rerun_evaluation(
            session=session,
            candidate_position_id=candidate_position.id,
            step_type=EvaluationStepType.cv_analysis,
        )

        mock_publish.assert_called_once_with(
            evaluation_id=result[0].id,
            candidate_position_id=candidate_position.id,
            step_type=EvaluationStepType.cv_analysis,
            source_document_id=10,
            rubric_version_id=5,
        )

    @patch(_PUBLISH_PATH, new_callable=AsyncMock)
    async def test_rerun_cv_analysis_with_completed_technical_cascades_rec(
        self,
        mock_publish: AsyncMock,
        session: AsyncSession,
        candidate_position: CandidatePosition,
    ) -> None:
        await _seed_evaluation(
            session,
            candidate_position.id,
            EvaluationStepType.cv_analysis,
        )
        await _seed_evaluation(
            session,
            candidate_position.id,
            EvaluationStepType.technical_eval,
            status=EvaluationStatus.completed,
        )

        result = await evaluation_service.rerun_evaluation(
            session=session,
            candidate_position_id=candidate_position.id,
            step_type=EvaluationStepType.cv_analysis,
        )

        assert len(result) == 2
        step_types = {e.step_type for e in result}
        assert EvaluationStepType.cv_analysis in step_types
        assert EvaluationStepType.recommendation in step_types

        rec = next(
            e for e in result if e.step_type == EvaluationStepType.recommendation
        )
        assert rec.status == EvaluationStatus.pending
        assert rec.version == 1
        assert mock_publish.call_count == 2

    @patch(_PUBLISH_PATH, new_callable=AsyncMock)
    async def test_rerun_cv_analysis_without_completed_technical_eval_no_cascade(
        self,
        mock_publish: AsyncMock,
        session: AsyncSession,
        candidate_position: CandidatePosition,
    ) -> None:
        await _seed_evaluation(
            session,
            candidate_position.id,
            EvaluationStepType.cv_analysis,
        )
        await _seed_evaluation(
            session,
            candidate_position.id,
            EvaluationStepType.technical_eval,
            status=EvaluationStatus.pending,
        )

        result = await evaluation_service.rerun_evaluation(
            session=session,
            candidate_position_id=candidate_position.id,
            step_type=EvaluationStepType.cv_analysis,
        )

        assert len(result) == 1
        assert result[0].step_type == EvaluationStepType.cv_analysis
        mock_publish.assert_called_once()

    @patch(_PUBLISH_PATH, new_callable=AsyncMock)
    async def test_rerun_screening_eval_with_completed_technical_cascades_rec(
        self,
        mock_publish: AsyncMock,
        session: AsyncSession,
        candidate_position: CandidatePosition,
    ) -> None:
        await _seed_evaluation(
            session,
            candidate_position.id,
            EvaluationStepType.screening_eval,
        )
        await _seed_evaluation(
            session,
            candidate_position.id,
            EvaluationStepType.technical_eval,
            status=EvaluationStatus.completed,
        )

        result = await evaluation_service.rerun_evaluation(
            session=session,
            candidate_position_id=candidate_position.id,
            step_type=EvaluationStepType.screening_eval,
        )

        assert len(result) == 2
        step_types = {e.step_type for e in result}
        assert EvaluationStepType.screening_eval in step_types
        assert EvaluationStepType.recommendation in step_types

    @patch(_PUBLISH_PATH, new_callable=AsyncMock)
    async def test_rerun_technical_eval_always_cascades_recommendation(
        self,
        mock_publish: AsyncMock,
        session: AsyncSession,
        candidate_position: CandidatePosition,
    ) -> None:
        await _seed_evaluation(
            session,
            candidate_position.id,
            EvaluationStepType.technical_eval,
        )

        result = await evaluation_service.rerun_evaluation(
            session=session,
            candidate_position_id=candidate_position.id,
            step_type=EvaluationStepType.technical_eval,
        )

        assert len(result) == 2
        step_types = {e.step_type for e in result}
        assert EvaluationStepType.technical_eval in step_types
        assert EvaluationStepType.recommendation in step_types
        assert mock_publish.call_count == 2

    @patch(_PUBLISH_PATH, new_callable=AsyncMock)
    async def test_rerun_technical_eval_cascade_increments_existing_rec_version(
        self,
        mock_publish: AsyncMock,
        session: AsyncSession,
        candidate_position: CandidatePosition,
    ) -> None:
        await _seed_evaluation(
            session,
            candidate_position.id,
            EvaluationStepType.technical_eval,
        )
        await _seed_evaluation(
            session,
            candidate_position.id,
            EvaluationStepType.recommendation,
            source_document_id=None,
            rubric_version_id=None,
        )

        result = await evaluation_service.rerun_evaluation(
            session=session,
            candidate_position_id=candidate_position.id,
            step_type=EvaluationStepType.technical_eval,
        )

        rec = next(
            e for e in result if e.step_type == EvaluationStepType.recommendation
        )
        assert rec.version == 2

    @patch(_PUBLISH_PATH, new_callable=AsyncMock)
    async def test_rerun_recommendation_has_no_cascade(
        self,
        mock_publish: AsyncMock,
        session: AsyncSession,
        candidate_position: CandidatePosition,
    ) -> None:
        await _seed_evaluation(
            session,
            candidate_position.id,
            EvaluationStepType.recommendation,
            source_document_id=None,
            rubric_version_id=None,
        )

        result = await evaluation_service.rerun_evaluation(
            session=session,
            candidate_position_id=candidate_position.id,
            step_type=EvaluationStepType.recommendation,
        )

        assert len(result) == 1
        assert result[0].step_type == EvaluationStepType.recommendation
        assert result[0].version == 2
        mock_publish.assert_called_once()

    @patch(_PUBLISH_PATH, new_callable=AsyncMock)
    async def test_rerun_feedback_gen_has_no_cascade(
        self,
        mock_publish: AsyncMock,
        session: AsyncSession,
        candidate_position: CandidatePosition,
    ) -> None:
        await _seed_evaluation(
            session,
            candidate_position.id,
            EvaluationStepType.feedback_gen,
            source_document_id=None,
            rubric_version_id=None,
        )

        result = await evaluation_service.rerun_evaluation(
            session=session,
            candidate_position_id=candidate_position.id,
            step_type=EvaluationStepType.feedback_gen,
        )

        assert len(result) == 1
        assert result[0].step_type == EvaluationStepType.feedback_gen
        mock_publish.assert_called_once()

    async def test_rerun_raises_not_found_when_no_evaluation_exists(
        self,
        session: AsyncSession,
        candidate_position: CandidatePosition,
    ) -> None:
        with pytest.raises(NotFoundException):
            await evaluation_service.rerun_evaluation(
                session=session,
                candidate_position_id=candidate_position.id,
                step_type=EvaluationStepType.cv_analysis,
            )

    @patch(_PUBLISH_PATH, new_callable=AsyncMock)
    async def test_old_versions_preserved_in_history(
        self,
        mock_publish: AsyncMock,
        session: AsyncSession,
        candidate_position: CandidatePosition,
    ) -> None:
        await _seed_evaluation(
            session,
            candidate_position.id,
            EvaluationStepType.cv_analysis,
        )

        await evaluation_service.rerun_evaluation(
            session=session,
            candidate_position_id=candidate_position.id,
            step_type=EvaluationStepType.cv_analysis,
        )

        history = await evaluation_service.get_evaluation_history(
            session=session,
            candidate_position_id=candidate_position.id,
            step_type=EvaluationStepType.cv_analysis,
        )

        assert len(history) == 2
        assert history[0].version == 2
        assert history[1].version == 1


class TestRerunEvaluationEndpoint:
    @patch(_PUBLISH_PATH, new_callable=AsyncMock)
    async def test_post_rerun_returns_200_with_created_evaluations(
        self,
        mock_publish: AsyncMock,
        authenticated_client: AsyncClient,
        session: AsyncSession,
        candidate_position: CandidatePosition,
    ) -> None:
        await _seed_evaluation(
            session,
            candidate_position.id,
            EvaluationStepType.cv_analysis,
        )

        response = await authenticated_client.post(
            f"/api/evaluations/{candidate_position.id}/{EvaluationStepType.cv_analysis}/rerun"
        )

        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert len(data["items"]) == 1
        item = data["items"][0]
        assert item["step_type"] == EvaluationStepType.cv_analysis
        assert item["version"] == 2
        assert item["status"] == EvaluationStatus.pending

    @patch(_PUBLISH_PATH, new_callable=AsyncMock)
    async def test_post_rerun_returns_404_when_no_prior_evaluation(
        self,
        mock_publish: AsyncMock,
        authenticated_client: AsyncClient,
        candidate_position: CandidatePosition,
    ) -> None:
        response = await authenticated_client.post(
            f"/api/evaluations/{candidate_position.id}/{EvaluationStepType.cv_analysis}/rerun"
        )

        assert response.status_code == 404

    async def test_post_rerun_requires_authentication(
        self,
        client: AsyncClient,
        candidate_position: CandidatePosition,
    ) -> None:
        response = await client.post(
            f"/api/evaluations/{candidate_position.id}/{EvaluationStepType.cv_analysis}/rerun"
        )

        assert response.status_code == 401

    @patch(_PUBLISH_PATH, new_callable=AsyncMock)
    async def test_post_rerun_technical_eval_returns_two_items_with_cascade(
        self,
        mock_publish: AsyncMock,
        authenticated_client: AsyncClient,
        session: AsyncSession,
        candidate_position: CandidatePosition,
    ) -> None:
        await _seed_evaluation(
            session,
            candidate_position.id,
            EvaluationStepType.technical_eval,
        )

        response = await authenticated_client.post(
            f"/api/evaluations/{candidate_position.id}/{EvaluationStepType.technical_eval}/rerun"
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 2
        step_types = {item["step_type"] for item in data["items"]}
        assert EvaluationStepType.technical_eval in step_types
        assert EvaluationStepType.recommendation in step_types

    @patch(_PUBLISH_PATH, new_callable=AsyncMock)
    async def test_history_endpoint_shows_all_versions_after_rerun(
        self,
        mock_publish: AsyncMock,
        authenticated_client: AsyncClient,
        session: AsyncSession,
        candidate_position: CandidatePosition,
    ) -> None:
        await _seed_evaluation(
            session,
            candidate_position.id,
            EvaluationStepType.cv_analysis,
        )

        await authenticated_client.post(
            f"/api/evaluations/{candidate_position.id}/{EvaluationStepType.cv_analysis}/rerun"
        )

        response = await authenticated_client.get(
            f"/api/evaluations/{candidate_position.id}/{EvaluationStepType.cv_analysis}/history"
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 2
        assert data["items"][0]["version"] == 2
        assert data["items"][1]["version"] == 1
