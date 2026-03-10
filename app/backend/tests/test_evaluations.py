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


@pytest.fixture
async def candidate_position(session: AsyncSession) -> CandidatePosition:
    candidate = Candidate(full_name="Alice Johnson", email="alice@example.com")
    session.add(candidate)
    await session.flush()

    team = Team(name="Engineering")
    session.add(team)
    await session.flush()

    user = User(
        email="hm@provectus.com",
        google_id="hm-eval-123",
        full_name="Hiring Manager",
    )
    session.add(user)
    await session.flush()

    position = Position(
        title="Backend Engineer",
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


class TestEvaluationModel:
    async def test_creates_evaluation_with_all_fields(
        self, session: AsyncSession, candidate_position: CandidatePosition
    ) -> None:
        evaluation = Evaluation(
            candidate_position_id=candidate_position.id,
            step_type=EvaluationStepType.cv_analysis,
            status=EvaluationStatus.pending,
            version=1,
            result={"score": 85, "summary": "Strong candidate"},
            error_message=None,
        )
        session.add(evaluation)
        await session.commit()
        await session.refresh(evaluation)

        assert evaluation.id is not None
        assert evaluation.candidate_position_id == candidate_position.id
        assert evaluation.step_type == EvaluationStepType.cv_analysis
        assert evaluation.status == EvaluationStatus.pending
        assert evaluation.version == 1
        assert evaluation.result == {"score": 85, "summary": "Strong candidate"}
        assert evaluation.error_message is None
        assert evaluation.source_document_id is None
        assert evaluation.rubric_version_id is None
        assert evaluation.created_at is not None


class TestCreateEvaluation:
    async def test_creates_evaluation_with_pending_status_and_version_one(
        self, session: AsyncSession, candidate_position: CandidatePosition
    ) -> None:
        evaluation = await evaluation_service.create_evaluation(
            session=session,
            candidate_position_id=candidate_position.id,
            step_type=EvaluationStepType.cv_analysis,
        )

        assert evaluation.id is not None
        assert evaluation.candidate_position_id == candidate_position.id
        assert evaluation.step_type == EvaluationStepType.cv_analysis
        assert evaluation.status == EvaluationStatus.pending
        assert evaluation.version == 1

    async def test_second_create_for_same_step_increments_version(
        self, session: AsyncSession, candidate_position: CandidatePosition
    ) -> None:
        first = await evaluation_service.create_evaluation(
            session=session,
            candidate_position_id=candidate_position.id,
            step_type=EvaluationStepType.screening_eval,
        )
        second = await evaluation_service.create_evaluation(
            session=session,
            candidate_position_id=candidate_position.id,
            step_type=EvaluationStepType.screening_eval,
        )

        assert first.version == 1
        assert second.version == 2

    async def test_version_is_independent_per_step_type(
        self, session: AsyncSession, candidate_position: CandidatePosition
    ) -> None:
        cv_eval = await evaluation_service.create_evaluation(
            session=session,
            candidate_position_id=candidate_position.id,
            step_type=EvaluationStepType.cv_analysis,
        )
        screening_eval = await evaluation_service.create_evaluation(
            session=session,
            candidate_position_id=candidate_position.id,
            step_type=EvaluationStepType.screening_eval,
        )

        assert cv_eval.version == 1
        assert screening_eval.version == 1

    async def test_raises_not_found_for_missing_candidate_position(
        self, session: AsyncSession
    ) -> None:
        with pytest.raises(NotFoundException):
            await evaluation_service.create_evaluation(
                session=session,
                candidate_position_id=99999,
                step_type=EvaluationStepType.cv_analysis,
            )

    async def test_stores_optional_source_document_and_rubric_version(
        self, session: AsyncSession, candidate_position: CandidatePosition
    ) -> None:
        evaluation = await evaluation_service.create_evaluation(
            session=session,
            candidate_position_id=candidate_position.id,
            step_type=EvaluationStepType.cv_analysis,
            source_document_id=42,
            rubric_version_id=7,
        )

        assert evaluation.source_document_id == 42
        assert evaluation.rubric_version_id == 7


class TestGetEvaluations:
    async def test_returns_empty_list_when_no_evaluations_exist(
        self, session: AsyncSession, candidate_position: CandidatePosition
    ) -> None:
        evaluations = await evaluation_service.get_evaluations(
            session=session,
            candidate_position_id=candidate_position.id,
        )

        assert evaluations == []

    async def test_returns_one_entry_per_step_type(
        self, session: AsyncSession, candidate_position: CandidatePosition
    ) -> None:
        await evaluation_service.create_evaluation(
            session=session,
            candidate_position_id=candidate_position.id,
            step_type=EvaluationStepType.cv_analysis,
        )
        await evaluation_service.create_evaluation(
            session=session,
            candidate_position_id=candidate_position.id,
            step_type=EvaluationStepType.screening_eval,
        )

        evaluations = await evaluation_service.get_evaluations(
            session=session,
            candidate_position_id=candidate_position.id,
        )

        assert len(evaluations) == 2
        step_types = {e.step_type for e in evaluations}
        assert EvaluationStepType.cv_analysis in step_types
        assert EvaluationStepType.screening_eval in step_types

    async def test_returns_only_latest_version_per_step_type(
        self, session: AsyncSession, candidate_position: CandidatePosition
    ) -> None:
        await evaluation_service.create_evaluation(
            session=session,
            candidate_position_id=candidate_position.id,
            step_type=EvaluationStepType.cv_analysis,
        )
        second = await evaluation_service.create_evaluation(
            session=session,
            candidate_position_id=candidate_position.id,
            step_type=EvaluationStepType.cv_analysis,
        )

        evaluations = await evaluation_service.get_evaluations(
            session=session,
            candidate_position_id=candidate_position.id,
        )

        assert len(evaluations) == 1
        assert evaluations[0].version == second.version


class TestGetEvaluationByStep:
    async def test_returns_latest_version_for_step(
        self, session: AsyncSession, candidate_position: CandidatePosition
    ) -> None:
        await evaluation_service.create_evaluation(
            session=session,
            candidate_position_id=candidate_position.id,
            step_type=EvaluationStepType.cv_analysis,
        )
        second = await evaluation_service.create_evaluation(
            session=session,
            candidate_position_id=candidate_position.id,
            step_type=EvaluationStepType.cv_analysis,
        )

        result = await evaluation_service.get_evaluation_by_step(
            session=session,
            candidate_position_id=candidate_position.id,
            step_type=EvaluationStepType.cv_analysis,
        )

        assert result.id == second.id
        assert result.version == 2

    async def test_raises_not_found_when_no_evaluation_for_step(
        self, session: AsyncSession, candidate_position: CandidatePosition
    ) -> None:
        with pytest.raises(NotFoundException):
            await evaluation_service.get_evaluation_by_step(
                session=session,
                candidate_position_id=candidate_position.id,
                step_type=EvaluationStepType.cv_analysis,
            )


class TestGetEvaluationHistory:
    async def test_returns_all_versions_ordered_by_version_desc(
        self, session: AsyncSession, candidate_position: CandidatePosition
    ) -> None:
        first = await evaluation_service.create_evaluation(
            session=session,
            candidate_position_id=candidate_position.id,
            step_type=EvaluationStepType.cv_analysis,
        )
        second = await evaluation_service.create_evaluation(
            session=session,
            candidate_position_id=candidate_position.id,
            step_type=EvaluationStepType.cv_analysis,
        )
        third = await evaluation_service.create_evaluation(
            session=session,
            candidate_position_id=candidate_position.id,
            step_type=EvaluationStepType.cv_analysis,
        )

        history = await evaluation_service.get_evaluation_history(
            session=session,
            candidate_position_id=candidate_position.id,
            step_type=EvaluationStepType.cv_analysis,
        )

        assert len(history) == 3
        assert history[0].id == third.id
        assert history[1].id == second.id
        assert history[2].id == first.id
        assert [h.version for h in history] == [3, 2, 1]

    async def test_returns_empty_list_for_step_with_no_history(
        self, session: AsyncSession, candidate_position: CandidatePosition
    ) -> None:
        history = await evaluation_service.get_evaluation_history(
            session=session,
            candidate_position_id=candidate_position.id,
            step_type=EvaluationStepType.cv_analysis,
        )

        assert history == []

    async def test_isolates_history_by_step_type(
        self, session: AsyncSession, candidate_position: CandidatePosition
    ) -> None:
        await evaluation_service.create_evaluation(
            session=session,
            candidate_position_id=candidate_position.id,
            step_type=EvaluationStepType.cv_analysis,
        )
        await evaluation_service.create_evaluation(
            session=session,
            candidate_position_id=candidate_position.id,
            step_type=EvaluationStepType.cv_analysis,
        )
        await evaluation_service.create_evaluation(
            session=session,
            candidate_position_id=candidate_position.id,
            step_type=EvaluationStepType.screening_eval,
        )

        cv_history = await evaluation_service.get_evaluation_history(
            session=session,
            candidate_position_id=candidate_position.id,
            step_type=EvaluationStepType.cv_analysis,
        )
        screening_history = await evaluation_service.get_evaluation_history(
            session=session,
            candidate_position_id=candidate_position.id,
            step_type=EvaluationStepType.screening_eval,
        )

        assert len(cv_history) == 2
        assert len(screening_history) == 1


class TestListEvaluationsEndpoint:
    async def test_returns_empty_list_when_no_evaluations_exist(
        self, authenticated_client: AsyncClient, candidate_position: CandidatePosition
    ) -> None:
        response = await authenticated_client.get(
            f"/api/evaluations/{candidate_position.id}"
        )

        assert response.status_code == 200
        data = response.json()
        assert data == {"items": []}

    async def test_returns_evaluations_after_creating_some(
        self,
        authenticated_client: AsyncClient,
        session: AsyncSession,
        candidate_position: CandidatePosition,
    ) -> None:
        await evaluation_service.create_evaluation(
            session=session,
            candidate_position_id=candidate_position.id,
            step_type=EvaluationStepType.cv_analysis,
        )
        await evaluation_service.create_evaluation(
            session=session,
            candidate_position_id=candidate_position.id,
            step_type=EvaluationStepType.screening_eval,
        )

        response = await authenticated_client.get(
            f"/api/evaluations/{candidate_position.id}"
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 2
        step_types = {item["step_type"] for item in data["items"]}
        assert EvaluationStepType.cv_analysis in step_types
        assert EvaluationStepType.screening_eval in step_types

    async def test_response_shape_includes_required_fields(
        self,
        authenticated_client: AsyncClient,
        session: AsyncSession,
        candidate_position: CandidatePosition,
    ) -> None:
        await evaluation_service.create_evaluation(
            session=session,
            candidate_position_id=candidate_position.id,
            step_type=EvaluationStepType.cv_analysis,
        )

        response = await authenticated_client.get(
            f"/api/evaluations/{candidate_position.id}"
        )

        assert response.status_code == 200
        item = response.json()["items"][0]
        assert "id" in item
        assert "step_type" in item
        assert "status" in item
        assert "version" in item
        assert "created_at" in item
        assert item["status"] == EvaluationStatus.pending
        assert item["version"] == 1

    async def test_requires_authentication(
        self, client: AsyncClient, candidate_position: CandidatePosition
    ) -> None:
        response = await client.get(f"/api/evaluations/{candidate_position.id}")

        assert response.status_code == 401


class TestGetEvaluationByStepEndpoint:
    async def test_returns_404_when_no_evaluation_exists_for_step(
        self, authenticated_client: AsyncClient, candidate_position: CandidatePosition
    ) -> None:
        response = await authenticated_client.get(
            f"/api/evaluations/{candidate_position.id}/{EvaluationStepType.cv_analysis}"
        )

        assert response.status_code == 404
        assert "detail" in response.json()

    async def test_returns_latest_evaluation_for_step(
        self,
        authenticated_client: AsyncClient,
        session: AsyncSession,
        candidate_position: CandidatePosition,
    ) -> None:
        await evaluation_service.create_evaluation(
            session=session,
            candidate_position_id=candidate_position.id,
            step_type=EvaluationStepType.cv_analysis,
        )
        second = await evaluation_service.create_evaluation(
            session=session,
            candidate_position_id=candidate_position.id,
            step_type=EvaluationStepType.cv_analysis,
        )

        response = await authenticated_client.get(
            f"/api/evaluations/{candidate_position.id}/{EvaluationStepType.cv_analysis}"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == second.id
        assert data["version"] == 2
        assert data["step_type"] == EvaluationStepType.cv_analysis

    async def test_requires_authentication(
        self, client: AsyncClient, candidate_position: CandidatePosition
    ) -> None:
        response = await client.get(
            f"/api/evaluations/{candidate_position.id}/{EvaluationStepType.cv_analysis}"
        )

        assert response.status_code == 401


class TestGetEvaluationHistoryEndpoint:
    async def test_returns_all_versions_for_step(
        self,
        authenticated_client: AsyncClient,
        session: AsyncSession,
        candidate_position: CandidatePosition,
    ) -> None:
        for _ in range(3):
            await evaluation_service.create_evaluation(
                session=session,
                candidate_position_id=candidate_position.id,
                step_type=EvaluationStepType.cv_analysis,
            )

        response = await authenticated_client.get(
            f"/api/evaluations/{candidate_position.id}/{EvaluationStepType.cv_analysis}/history"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["step_type"] == EvaluationStepType.cv_analysis
        assert len(data["items"]) == 3
        assert [item["version"] for item in data["items"]] == [3, 2, 1]

    async def test_returns_empty_items_for_step_with_no_history(
        self,
        authenticated_client: AsyncClient,
        candidate_position: CandidatePosition,
    ) -> None:
        response = await authenticated_client.get(
            f"/api/evaluations/{candidate_position.id}/{EvaluationStepType.cv_analysis}/history"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["step_type"] == EvaluationStepType.cv_analysis
        assert data["items"] == []

    async def test_isolates_history_by_step_type(
        self,
        authenticated_client: AsyncClient,
        session: AsyncSession,
        candidate_position: CandidatePosition,
    ) -> None:
        await evaluation_service.create_evaluation(
            session=session,
            candidate_position_id=candidate_position.id,
            step_type=EvaluationStepType.cv_analysis,
        )
        await evaluation_service.create_evaluation(
            session=session,
            candidate_position_id=candidate_position.id,
            step_type=EvaluationStepType.cv_analysis,
        )
        await evaluation_service.create_evaluation(
            session=session,
            candidate_position_id=candidate_position.id,
            step_type=EvaluationStepType.screening_eval,
        )

        response = await authenticated_client.get(
            f"/api/evaluations/{candidate_position.id}/{EvaluationStepType.cv_analysis}/history"
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 2
        assert all(
            item["step_type"] == EvaluationStepType.cv_analysis
            for item in data["items"]
        )

    async def test_requires_authentication(
        self, client: AsyncClient, candidate_position: CandidatePosition
    ) -> None:
        response = await client.get(
            f"/api/evaluations/{candidate_position.id}/{EvaluationStepType.cv_analysis}/history"
        )

        assert response.status_code == 401
