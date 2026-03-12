import os
import re
from contextlib import contextmanager
from unittest.mock import MagicMock, patch

os.environ.setdefault("DB_HOST", "localhost")
os.environ.setdefault("DB_NAME", "test")
os.environ.setdefault("DB_USERNAME", "test")
os.environ.setdefault("DB_PASSWORD", "test")
os.environ.setdefault("S3_BUCKET_NAME", "test-bucket")
os.environ.setdefault("BEDROCK_MODEL_ID", "anthropic.claude-haiku-4-5-20251001-v1:0")
os.environ.setdefault("AWS_REGION", "us-east-1")

SAMPLE_SCREENING_RESULT = {
    "key_topics": ["Python", "distributed systems"],
    "strengths": ["Strong communication skills", "Clear problem-solving approach"],
    "concerns": ["Limited cloud experience"],
    "communication_quality": "Candidate communicated clearly throughout.",
    "motivation_culture_fit": "Shows genuine interest in the role.",
}

SAMPLE_TECHNICAL_RESULT = {
    "criteria_scores": [],
    "weighted_total": 3.2,
    "strengths_summary": ["System design knowledge", "Clean code practices"],
    "improvement_areas": ["Algorithm optimization", "Testing practices"],
}

SAMPLE_CV_RESULT = {
    "strengths": ["Relevant experience", "Strong educational background"],
    "gaps": ["No prior team lead experience"],
    "overall_impression": "Solid background for a mid-level role.",
}

SAMPLE_LLM_FEEDBACK = {
    "feedback_text": (
        "Thank you for taking the time to interview with us. We were impressed by your "
        "communication clarity and problem-solving approach demonstrated throughout our "
        "discussions. While we enjoyed learning about your background, we have decided "
        "to move forward with candidates who more closely match our current needs. "
        "To strengthen future applications, we encourage you to deepen your hands-on "
        "experience with cloud-native architectures and distributed systems at scale. "
        "We appreciate your interest and wish you the best in your search."
    ),
    "rejection_stage": "screening",
}


def _make_mock_evaluation(
    evaluation_id: int = 1,
    candidate_position_id: int = 5,
    step_type: str = "feedback_gen",
) -> MagicMock:
    evaluation = MagicMock()
    evaluation.id = evaluation_id
    evaluation.status = "pending"
    evaluation.candidate_position_id = candidate_position_id
    evaluation.step_type = step_type
    evaluation.source_document_id = None
    evaluation.rubric_version_id = None
    evaluation.result = None
    evaluation.error_message = None
    evaluation.started_at = None
    evaluation.completed_at = None
    return evaluation


def _make_completed_eval_row(step_type: str, result: dict) -> MagicMock:
    row = MagicMock()
    row.step_type = step_type
    row.status = "completed"
    row.result = result
    return row


def _make_session_mock(
    evaluation: MagicMock,
    completed_evals: dict[str, dict],
) -> MagicMock:
    session = MagicMock()

    def session_get(model_class, pk):
        if model_class.__name__ == "Evaluation":
            return evaluation
        return None

    session.get.side_effect = session_get

    def execute_side_effect(stmt):
        scalar_result = MagicMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None

        compiled = str(stmt.compile(compile_kwargs={"literal_binds": True}))

        for step_type, result in completed_evals.items():
            if step_type in compiled:
                row = _make_completed_eval_row(step_type, result)
                mock_result.scalar_one_or_none.return_value = row
                break

        return mock_result

    session.execute.side_effect = execute_side_effect
    return session


@contextmanager
def _mock_session(session: MagicMock):
    yield session


class TestFeedbackGenHandlerSuccess:
    def test_normal_flow_screening_rejection(self):
        from feedback_gen import handler as handler_module

        evaluation = _make_mock_evaluation()
        completed_evals = {
            "screening_eval": SAMPLE_SCREENING_RESULT,
            "cv_analysis": SAMPLE_CV_RESULT,
        }
        session = _make_session_mock(evaluation, completed_evals)

        with (
            patch(
                "shared.db.get_session",
                return_value=_mock_session(session),
            ),
            patch.object(
                handler_module.bedrock_module,
                "invoke_claude_structured",
                return_value=SAMPLE_LLM_FEEDBACK,
            ),
        ):
            result = handler_module.handler(
                {"detail": {"evaluation_id": 1}}, context=None
            )

        assert "feedback_text" in result
        assert len(result["feedback_text"]) > 50
        assert evaluation.status == "completed"
        assert evaluation.completed_at is not None
        assert evaluation.result is not None

    def test_normal_flow_technical_rejection(self):
        from feedback_gen import handler as handler_module

        technical_feedback = {
            "feedback_text": (
                "We appreciated your technical knowledge and strong system design instincts. "
                "However, we believe further practice with algorithmic optimization and "
                "test-driven development would strengthen your candidacy. We encourage you "
                "to revisit these areas and apply again in the future."
            ),
            "rejection_stage": "technical",
        }

        evaluation = _make_mock_evaluation()
        completed_evals = {
            "cv_analysis": SAMPLE_CV_RESULT,
            "screening_eval": SAMPLE_SCREENING_RESULT,
            "technical_eval": SAMPLE_TECHNICAL_RESULT,
        }
        session = _make_session_mock(evaluation, completed_evals)

        with (
            patch(
                "shared.db.get_session",
                return_value=_mock_session(session),
            ),
            patch.object(
                handler_module.bedrock_module,
                "invoke_claude_structured",
                return_value=technical_feedback,
            ),
        ):
            result = handler_module.handler(
                {"detail": {"evaluation_id": 1}}, context=None
            )

        assert result["rejection_stage"] == "technical"
        assert evaluation.status == "completed"

    def test_handles_missing_evaluation_results_gracefully(self):
        from feedback_gen import handler as handler_module

        evaluation = _make_mock_evaluation()
        session = _make_session_mock(evaluation, completed_evals={})

        minimal_feedback = {
            "feedback_text": (
                "Thank you for your interest. After careful consideration we have decided "
                "to move forward with other candidates. We encourage you to continue "
                "developing your skills and apply again in the future."
            ),
            "rejection_stage": "screening",
        }

        with (
            patch(
                "shared.db.get_session",
                return_value=_mock_session(session),
            ),
            patch.object(
                handler_module.bedrock_module,
                "invoke_claude_structured",
                return_value=minimal_feedback,
            ),
        ):
            result = handler_module.handler(
                {"detail": {"evaluation_id": 1}}, context=None
            )

        assert "feedback_text" in result
        assert evaluation.status == "completed"

    def test_sets_running_status_before_completed(self):
        from feedback_gen import handler as handler_module

        evaluation = _make_mock_evaluation()
        session = _make_session_mock(evaluation, completed_evals={})

        status_sequence: list[str] = []

        def tracking_add(obj):
            if hasattr(obj, "status"):
                status_sequence.append(obj.status)

        session.add.side_effect = tracking_add

        with (
            patch(
                "shared.db.get_session",
                return_value=_mock_session(session),
            ),
            patch.object(
                handler_module.bedrock_module,
                "invoke_claude_structured",
                return_value=SAMPLE_LLM_FEEDBACK,
            ),
        ):
            handler_module.handler({"detail": {"evaluation_id": 1}}, context=None)

        assert "running" in status_sequence
        assert status_sequence.index("running") < status_sequence.index("completed")


class TestFeedbackDoesNotExposeInternalDetails:
    def test_feedback_contains_no_numeric_scores(self):
        from feedback_gen import handler as handler_module

        feedback_with_no_scores = {
            "feedback_text": (
                "Your background demonstrated strong communication skills and a clear "
                "understanding of software engineering principles. We encourage you to "
                "deepen your expertise in cloud infrastructure and distributed systems "
                "design. Thank you for your time and we wish you well."
            ),
            "rejection_stage": "screening",
        }

        evaluation = _make_mock_evaluation()
        completed_evals = {"screening_eval": SAMPLE_SCREENING_RESULT}
        session = _make_session_mock(evaluation, completed_evals)

        with (
            patch(
                "shared.db.get_session",
                return_value=_mock_session(session),
            ),
            patch.object(
                handler_module.bedrock_module,
                "invoke_claude_structured",
                return_value=feedback_with_no_scores,
            ),
        ):
            result = handler_module.handler(
                {"detail": {"evaluation_id": 1}}, context=None
            )

        feedback_text = result["feedback_text"]
        numeric_score_pattern = re.compile(
            r"\b\d+(\.\d+)?\s*(\/\s*\d+|points?|%|score|rating|rated)\b",
            re.IGNORECASE,
        )
        assert not numeric_score_pattern.search(feedback_text), (
            f"Feedback contains a numeric score reference: {feedback_text}"
        )

    def test_feedback_contains_no_rubric_criterion_names(self):
        from feedback_gen import handler as handler_module

        rubric_criterion_feedback = {
            "feedback_text": (
                "You demonstrated strong interpersonal skills and thoughtful answers "
                "during our conversations. We recommend gaining more practical experience "
                "with complex system architectures. We appreciate you taking the time to "
                "speak with us."
            ),
            "rejection_stage": "technical",
        }

        rubric_criterion_names = ["System Design", "Coding", "Communication"]
        evaluation = _make_mock_evaluation()
        completed_evals = {"technical_eval": SAMPLE_TECHNICAL_RESULT}
        session = _make_session_mock(evaluation, completed_evals)

        with (
            patch(
                "shared.db.get_session",
                return_value=_mock_session(session),
            ),
            patch.object(
                handler_module.bedrock_module,
                "invoke_claude_structured",
                return_value=rubric_criterion_feedback,
            ),
        ):
            result = handler_module.handler(
                {"detail": {"evaluation_id": 1}}, context=None
            )

        feedback_text = result["feedback_text"]
        for criterion in rubric_criterion_names:
            assert criterion not in feedback_text, (
                f"Feedback exposes rubric criterion name '{criterion}': {feedback_text}"
            )


class TestFeedbackGenHandlerFailure:
    def test_sets_failed_on_bedrock_error(self):
        import pytest

        from feedback_gen import handler as handler_module

        evaluation = _make_mock_evaluation()
        session = _make_session_mock(evaluation, completed_evals={})

        with (
            patch(
                "shared.db.get_session",
                return_value=_mock_session(session),
            ),
            patch.object(
                handler_module.bedrock_module,
                "invoke_claude_structured",
                side_effect=RuntimeError("Bedrock throttled after retries"),
            ),
            pytest.raises(RuntimeError),
        ):
            handler_module.handler({"detail": {"evaluation_id": 1}}, context=None)

        assert evaluation.status == "failed"
        assert "Bedrock" in evaluation.error_message

    def test_sets_failed_when_evaluation_not_found(self):
        import pytest

        from feedback_gen import handler as handler_module

        session = MagicMock()
        session.get.return_value = None

        with (
            patch(
                "shared.db.get_session",
                return_value=_mock_session(session),
            ),
            pytest.raises(ValueError, match="not found"),
        ):
            handler_module.handler({"detail": {"evaluation_id": 999}}, context=None)
