import json
import os
from contextlib import contextmanager
from unittest.mock import MagicMock, patch

os.environ.setdefault("DB_HOST", "localhost")
os.environ.setdefault("DB_NAME", "test")
os.environ.setdefault("DB_USERNAME", "test")
os.environ.setdefault("DB_PASSWORD", "test")
os.environ.setdefault("S3_BUCKET_NAME", "test-bucket")
os.environ.setdefault("BEDROCK_MODEL_ID", "anthropic.claude-3-5-sonnet-20241022-v2:0")
os.environ.setdefault("AWS_REGION", "us-east-1")

CV_ANALYSIS_RESULT = {
    "skills_match": [
        {"skill": "Python", "present": True, "notes": "5 years experience"},
        {"skill": "FastAPI", "present": True, "notes": "Used in current role"},
    ],
    "experience_relevance": "Highly relevant backend experience.",
    "education": "BSc Computer Science.",
    "signals_and_red_flags": "Consistent career progression.",
    "overall_fit": "Strong fit for the role.",
}

SCREENING_EVAL_RESULT = {
    "key_topics": ["motivation", "remote work", "team fit"],
    "strengths": ["clear communicator", "strong motivation"],
    "concerns": ["no_significant_concerns"],
    "communication_quality": "Articulate and professional throughout.",
    "motivation_culture_fit": "Genuinely excited about the role and company values.",
}

TECHNICAL_EVAL_RESULT = {
    "criteria_scores": [
        {
            "criterion_name": "System Design",
            "category_name": "Architecture",
            "score": 4,
            "max_score": 5,
            "weight": 0.4,
            "evidence": "Designed a scalable microservices architecture",
            "reasoning": "Strong understanding of distributed systems",
        }
    ],
    "weighted_total": 0.8,
    "strengths_summary": ["Strong system design", "Good problem solving"],
    "improvement_areas": ["Could improve on low-level optimisation"],
}

FULL_RECOMMENDATION_RESULT = {
    "recommendation": "hire",
    "confidence": "high",
    "reasoning": "Candidate demonstrates strong skills across all evaluation dimensions.",
    "missing_inputs": [],
}

PARTIAL_RECOMMENDATION_RESULT = {
    "recommendation": "needs_discussion",
    "confidence": "low",
    "reasoning": "Only technical interview data available; CV and screening results are missing.",
    "missing_inputs": ["cv_analysis", "screening_eval"],
}

NO_INPUT_RECOMMENDATION_RESULT = {
    "recommendation": "needs_discussion",
    "confidence": "low",
    "reasoning": "No evaluation data is available to make a determination.",
    "missing_inputs": ["cv_analysis", "screening_eval", "technical_eval"],
}


def _make_mock_evaluation(evaluation_id: int = 1) -> MagicMock:
    evaluation = MagicMock()
    evaluation.id = evaluation_id
    evaluation.status = "pending"
    evaluation.source_document_id = None
    evaluation.candidate_position_id = 5
    evaluation.result = None
    evaluation.error_message = None
    evaluation.started_at = None
    evaluation.completed_at = None
    return evaluation


def _make_mock_candidate_position(cp_id: int = 5) -> MagicMock:
    cp = MagicMock()
    cp.id = cp_id
    cp.candidate_id = 1
    cp.position_id = 2
    return cp


def _make_mock_position(position_id: int = 2) -> MagicMock:
    pos = MagicMock()
    pos.id = position_id
    pos.title = "Senior Python Engineer"
    pos.requirements = "- Python\n- FastAPI\n- PostgreSQL"
    return pos



def _make_session_with_upstream(
    evaluation: MagicMock,
    candidate_position: MagicMock,
    position: MagicMock,
    cv_result: dict | None,
    screening_result: dict | None,
    technical_result: dict | None,
) -> MagicMock:
    """Build a session mock that routes query().filter().order_by().all() calls
    to the appropriate per-step result.

    The handler calls this chain once per step type in UPSTREAM_STEP_TYPES order
    (cv_analysis, screening_eval, technical_eval). We capture the step_type from
    the SQLAlchemy BinaryExpression argument passed to filter() and return the
    matching result row.
    """
    session = MagicMock()

    def session_get(model_class, pk):
        if model_class.__name__ == "Evaluation":
            return evaluation
        if model_class.__name__ == "CandidatePosition":
            return candidate_position
        if model_class.__name__ == "Position":
            return position
        return None

    session.get.side_effect = session_get

    results_by_step: dict[str, dict | None] = {
        "cv_analysis": cv_result,
        "screening_eval": screening_result,
        "technical_eval": technical_result,
    }

    step_order = ["cv_analysis", "screening_eval", "technical_eval"]
    call_index = [0]

    def query_side_effect(model_class):
        query_mock = MagicMock()

        def filter_side_effect(*args, **kwargs):
            filter_mock = MagicMock()
            current_index = call_index[0]
            call_index[0] += 1

            order_mock = MagicMock()

            def all_side_effect(captured_index=current_index):
                step = step_order[captured_index % 3]
                result = results_by_step.get(step)
                if result is None:
                    return []
                row = MagicMock()
                row.step_type = step
                row.status = "completed"
                row.result = result
                row.version = 1
                return [row]

            order_mock.all.side_effect = all_side_effect
            filter_mock.order_by.return_value = order_mock
            return filter_mock

        query_mock.filter.side_effect = filter_side_effect
        return query_mock

    session.query.side_effect = query_side_effect
    return session


@contextmanager
def _mock_session(session: MagicMock):
    yield session


class TestRecommendationHandlerAllInputsPresent:
    def test_all_inputs_available_produces_recommendation(self):
        from recommendation import handler as handler_module

        evaluation = _make_mock_evaluation()
        candidate_position = _make_mock_candidate_position()
        position = _make_mock_position()
        session = _make_session_with_upstream(
            evaluation,
            candidate_position,
            position,
            cv_result=CV_ANALYSIS_RESULT,
            screening_result=SCREENING_EVAL_RESULT,
            technical_result=TECHNICAL_EVAL_RESULT,
        )

        with (
            patch.object(
                handler_module.db_module,
                "get_session",
                return_value=_mock_session(session),
            ),
            patch.object(
                handler_module.bedrock_module,
                "invoke_claude",
                return_value=json.dumps(FULL_RECOMMENDATION_RESULT),
            ),
        ):
            result = handler_module.handler(
                {"detail": {"evaluation_id": 1}}, context=None
            )

        assert evaluation.status == "completed"
        assert result["recommendation"] in {"hire", "no_hire", "needs_discussion"}
        assert result["confidence"] in {"high", "medium", "low"}
        assert "reasoning" in result
        assert "missing_inputs" in result

    def test_all_inputs_present_allows_high_confidence(self):
        from recommendation import handler as handler_module

        evaluation = _make_mock_evaluation()
        candidate_position = _make_mock_candidate_position()
        position = _make_mock_position()
        session = _make_session_with_upstream(
            evaluation,
            candidate_position,
            position,
            cv_result=CV_ANALYSIS_RESULT,
            screening_result=SCREENING_EVAL_RESULT,
            technical_result=TECHNICAL_EVAL_RESULT,
        )

        bedrock_response = {
            "recommendation": "hire",
            "confidence": "high",
            "reasoning": "Strong candidate across all dimensions.",
            "missing_inputs": [],
        }

        with (
            patch.object(
                handler_module.db_module,
                "get_session",
                return_value=_mock_session(session),
            ),
            patch.object(
                handler_module.bedrock_module,
                "invoke_claude",
                return_value=json.dumps(bedrock_response),
            ),
        ):
            result = handler_module.handler(
                {"detail": {"evaluation_id": 1}}, context=None
            )

        assert result["confidence"] == "high"
        assert result["missing_inputs"] == []

    def test_sets_running_status_before_completed(self):
        from recommendation import handler as handler_module

        evaluation = _make_mock_evaluation()
        candidate_position = _make_mock_candidate_position()
        position = _make_mock_position()
        session = _make_session_with_upstream(
            evaluation,
            candidate_position,
            position,
            cv_result=CV_ANALYSIS_RESULT,
            screening_result=SCREENING_EVAL_RESULT,
            technical_result=TECHNICAL_EVAL_RESULT,
        )

        status_sequence: list[str] = []

        def tracking_add(obj):
            if hasattr(obj, "status"):
                status_sequence.append(obj.status)

        session.add.side_effect = tracking_add

        with (
            patch.object(
                handler_module.db_module,
                "get_session",
                return_value=_mock_session(session),
            ),
            patch.object(
                handler_module.bedrock_module,
                "invoke_claude",
                return_value=json.dumps(FULL_RECOMMENDATION_RESULT),
            ),
        ):
            handler_module.handler({"detail": {"evaluation_id": 1}}, context=None)

        assert "running" in status_sequence
        assert "completed" in status_sequence
        assert status_sequence.index("running") < status_sequence.index("completed")


class TestRecommendationHandlerMissingInputs:
    def test_only_technical_eval_available_forces_low_confidence(self):
        from recommendation import handler as handler_module

        evaluation = _make_mock_evaluation()
        candidate_position = _make_mock_candidate_position()
        position = _make_mock_position()
        session = _make_session_with_upstream(
            evaluation,
            candidate_position,
            position,
            cv_result=None,
            screening_result=None,
            technical_result=TECHNICAL_EVAL_RESULT,
        )

        bedrock_response = {
            "recommendation": "needs_discussion",
            "confidence": "medium",
            "reasoning": "Only technical eval available.",
            "missing_inputs": ["cv_analysis", "screening_eval"],
        }

        with (
            patch.object(
                handler_module.db_module,
                "get_session",
                return_value=_mock_session(session),
            ),
            patch.object(
                handler_module.bedrock_module,
                "invoke_claude",
                return_value=json.dumps(bedrock_response),
            ),
        ):
            result = handler_module.handler(
                {"detail": {"evaluation_id": 1}}, context=None
            )

        assert result["confidence"] == "low"
        assert "cv_analysis" in result["missing_inputs"]
        assert "screening_eval" in result["missing_inputs"]
        assert evaluation.status == "completed"

    def test_only_technical_eval_available_missing_inputs_lists_two(self):
        from recommendation import handler as handler_module

        evaluation = _make_mock_evaluation()
        candidate_position = _make_mock_candidate_position()
        position = _make_mock_position()
        session = _make_session_with_upstream(
            evaluation,
            candidate_position,
            position,
            cv_result=None,
            screening_result=None,
            technical_result=TECHNICAL_EVAL_RESULT,
        )

        with (
            patch.object(
                handler_module.db_module,
                "get_session",
                return_value=_mock_session(session),
            ),
            patch.object(
                handler_module.bedrock_module,
                "invoke_claude",
                return_value=json.dumps(PARTIAL_RECOMMENDATION_RESULT),
            ),
        ):
            result = handler_module.handler(
                {"detail": {"evaluation_id": 1}}, context=None
            )

        assert len(result["missing_inputs"]) == 2
        assert set(result["missing_inputs"]) == {"cv_analysis", "screening_eval"}

    def test_no_inputs_available_still_produces_recommendation(self):
        from recommendation import handler as handler_module

        evaluation = _make_mock_evaluation()
        candidate_position = _make_mock_candidate_position()
        position = _make_mock_position()
        session = _make_session_with_upstream(
            evaluation,
            candidate_position,
            position,
            cv_result=None,
            screening_result=None,
            technical_result=None,
        )

        with (
            patch.object(
                handler_module.db_module,
                "get_session",
                return_value=_mock_session(session),
            ),
            patch.object(
                handler_module.bedrock_module,
                "invoke_claude",
                return_value=json.dumps(NO_INPUT_RECOMMENDATION_RESULT),
            ),
        ):
            result = handler_module.handler(
                {"detail": {"evaluation_id": 1}}, context=None
            )

        assert evaluation.status == "completed"
        assert result["recommendation"] in {"hire", "no_hire", "needs_discussion"}
        assert result["confidence"] == "low"
        assert len(result["missing_inputs"]) == 3
        assert set(result["missing_inputs"]) == {"cv_analysis", "screening_eval", "technical_eval"}

    def test_no_inputs_server_enforces_low_confidence_regardless_of_bedrock(self):
        from recommendation import handler as handler_module

        evaluation = _make_mock_evaluation()
        candidate_position = _make_mock_candidate_position()
        position = _make_mock_position()
        session = _make_session_with_upstream(
            evaluation,
            candidate_position,
            position,
            cv_result=None,
            screening_result=None,
            technical_result=None,
        )

        bedrock_ignores_instruction = {
            "recommendation": "hire",
            "confidence": "high",
            "reasoning": "Bedrock incorrectly returned high confidence despite missing inputs.",
            "missing_inputs": [],
        }

        with (
            patch.object(
                handler_module.db_module,
                "get_session",
                return_value=_mock_session(session),
            ),
            patch.object(
                handler_module.bedrock_module,
                "invoke_claude",
                return_value=json.dumps(bedrock_ignores_instruction),
            ),
        ):
            result = handler_module.handler(
                {"detail": {"evaluation_id": 1}}, context=None
            )

        assert result["confidence"] == "low"


class TestRecommendationHandlerValidation:
    def test_invalid_recommendation_value_is_corrected_to_needs_discussion(self):
        from recommendation import handler as handler_module

        evaluation = _make_mock_evaluation()
        candidate_position = _make_mock_candidate_position()
        position = _make_mock_position()
        session = _make_session_with_upstream(
            evaluation,
            candidate_position,
            position,
            cv_result=CV_ANALYSIS_RESULT,
            screening_result=SCREENING_EVAL_RESULT,
            technical_result=TECHNICAL_EVAL_RESULT,
        )

        invalid_response = {
            "recommendation": "maybe",
            "confidence": "high",
            "reasoning": "Bedrock returned an unrecognised recommendation value.",
            "missing_inputs": [],
        }

        with (
            patch.object(
                handler_module.db_module,
                "get_session",
                return_value=_mock_session(session),
            ),
            patch.object(
                handler_module.bedrock_module,
                "invoke_claude",
                return_value=json.dumps(invalid_response),
            ),
        ):
            result = handler_module.handler(
                {"detail": {"evaluation_id": 1}}, context=None
            )

        assert result["recommendation"] == "needs_discussion"
        assert evaluation.status == "completed"

    def test_invalid_confidence_value_is_corrected_to_low(self):
        from recommendation import handler as handler_module

        evaluation = _make_mock_evaluation()
        candidate_position = _make_mock_candidate_position()
        position = _make_mock_position()
        session = _make_session_with_upstream(
            evaluation,
            candidate_position,
            position,
            cv_result=CV_ANALYSIS_RESULT,
            screening_result=SCREENING_EVAL_RESULT,
            technical_result=TECHNICAL_EVAL_RESULT,
        )

        invalid_response = {
            "recommendation": "hire",
            "confidence": "very_high",
            "reasoning": "Bedrock returned an unrecognised confidence value.",
            "missing_inputs": [],
        }

        with (
            patch.object(
                handler_module.db_module,
                "get_session",
                return_value=_mock_session(session),
            ),
            patch.object(
                handler_module.bedrock_module,
                "invoke_claude",
                return_value=json.dumps(invalid_response),
            ),
        ):
            result = handler_module.handler(
                {"detail": {"evaluation_id": 1}}, context=None
            )

        assert result["confidence"] == "low"
        assert evaluation.status == "completed"

    def test_bedrock_error_sets_evaluation_to_failed(self):
        import pytest

        from recommendation import handler as handler_module

        evaluation = _make_mock_evaluation()
        candidate_position = _make_mock_candidate_position()
        position = _make_mock_position()
        session = _make_session_with_upstream(
            evaluation,
            candidate_position,
            position,
            cv_result=CV_ANALYSIS_RESULT,
            screening_result=SCREENING_EVAL_RESULT,
            technical_result=TECHNICAL_EVAL_RESULT,
        )

        with (
            patch.object(
                handler_module.db_module,
                "get_session",
                return_value=_mock_session(session),
            ),
            patch.object(
                handler_module.bedrock_module,
                "invoke_claude",
                side_effect=RuntimeError("Bedrock throttled after retries"),
            ),
            pytest.raises(RuntimeError),
        ):
            handler_module.handler({"detail": {"evaluation_id": 1}}, context=None)

        assert evaluation.status == "failed"
        assert "Bedrock" in evaluation.error_message

    def test_handles_markdown_wrapped_json(self):
        from recommendation import handler as handler_module

        evaluation = _make_mock_evaluation()
        candidate_position = _make_mock_candidate_position()
        position = _make_mock_position()
        session = _make_session_with_upstream(
            evaluation,
            candidate_position,
            position,
            cv_result=CV_ANALYSIS_RESULT,
            screening_result=SCREENING_EVAL_RESULT,
            technical_result=TECHNICAL_EVAL_RESULT,
        )

        wrapped = f"```json\n{json.dumps(FULL_RECOMMENDATION_RESULT)}\n```"

        with (
            patch.object(
                handler_module.db_module,
                "get_session",
                return_value=_mock_session(session),
            ),
            patch.object(
                handler_module.bedrock_module,
                "invoke_claude",
                return_value=wrapped,
            ),
        ):
            result = handler_module.handler(
                {"detail": {"evaluation_id": 1}}, context=None
            )

        assert result["recommendation"] == "hire"
