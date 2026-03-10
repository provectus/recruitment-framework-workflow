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

SAMPLE_RESULT = {
    "key_topics": ["Python experience", "system design", "remote work"],
    "strengths": ["Strong async Python background", "Clear communication"],
    "concerns": ["Limited team leadership experience"],
    "communication_quality": "Candidate articulated ideas clearly and concisely throughout the interview.",
    "motivation_culture_fit": "Expressed genuine interest in the product domain and aligned with async-first culture.",
}

LONG_TRANSCRIPT = " ".join(["word"] * 150)
SHORT_TRANSCRIPT = " ".join(["word"] * 50)


def _make_mock_evaluation(evaluation_id: int = 1) -> MagicMock:
    evaluation = MagicMock()
    evaluation.id = evaluation_id
    evaluation.status = "pending"
    evaluation.source_document_id = 10
    evaluation.candidate_position_id = 5
    evaluation.result = None
    evaluation.error_message = None
    evaluation.started_at = None
    evaluation.completed_at = None
    return evaluation


def _make_mock_document(document_id: int = 10) -> MagicMock:
    doc = MagicMock()
    doc.id = document_id
    doc.s3_key = "uploads/transcript.txt"
    doc.candidate_position_id = 5
    return doc


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


def _make_session_mock(
    evaluation: MagicMock,
    document: MagicMock,
    candidate_position: MagicMock,
    position: MagicMock,
) -> MagicMock:
    session = MagicMock()

    def session_get(model_class, pk):
        if model_class.__name__ == "Evaluation":
            return evaluation
        if model_class.__name__ == "Document":
            return document
        if model_class.__name__ == "CandidatePosition":
            return candidate_position
        if model_class.__name__ == "Position":
            return position
        return None

    session.get.side_effect = session_get
    return session


@contextmanager
def _mock_session(session: MagicMock):
    yield session


class TestScreeningEvalHandlerSuccess:
    def test_all_five_sections_present_in_result(self):
        from screening_eval import handler as handler_module

        evaluation = _make_mock_evaluation()
        document = _make_mock_document()
        candidate_position = _make_mock_candidate_position()
        position = _make_mock_position()
        session = _make_session_mock(evaluation, document, candidate_position, position)

        with (
            patch.object(
                handler_module.db_module,
                "get_session",
                return_value=_mock_session(session),
            ),
            patch.object(
                handler_module.s3_module,
                "get_document_text",
                return_value=LONG_TRANSCRIPT,
            ),
            patch.object(
                handler_module.bedrock_module,
                "invoke_claude",
                return_value=json.dumps(SAMPLE_RESULT),
            ),
        ):
            result = handler_module.handler(
                {"detail": {"evaluation_id": 1}}, context=None
            )

        assert "key_topics" in result
        assert "strengths" in result
        assert "concerns" in result
        assert "communication_quality" in result
        assert "motivation_culture_fit" in result

    def test_completed_status_with_valid_result(self):
        from screening_eval import handler as handler_module

        evaluation = _make_mock_evaluation()
        document = _make_mock_document()
        candidate_position = _make_mock_candidate_position()
        position = _make_mock_position()
        session = _make_session_mock(evaluation, document, candidate_position, position)

        with (
            patch.object(
                handler_module.db_module,
                "get_session",
                return_value=_mock_session(session),
            ),
            patch.object(
                handler_module.s3_module,
                "get_document_text",
                return_value=LONG_TRANSCRIPT,
            ),
            patch.object(
                handler_module.bedrock_module,
                "invoke_claude",
                return_value=json.dumps(SAMPLE_RESULT),
            ),
        ):
            result = handler_module.handler(
                {"detail": {"evaluation_id": 1}}, context=None
            )

        assert evaluation.status == "completed"
        assert evaluation.result == SAMPLE_RESULT
        assert evaluation.completed_at is not None
        assert result == SAMPLE_RESULT

    def test_handles_markdown_wrapped_json(self):
        from screening_eval import handler as handler_module

        evaluation = _make_mock_evaluation()
        document = _make_mock_document()
        candidate_position = _make_mock_candidate_position()
        position = _make_mock_position()
        session = _make_session_mock(evaluation, document, candidate_position, position)

        wrapped = f"```json\n{json.dumps(SAMPLE_RESULT)}\n```"

        with (
            patch.object(
                handler_module.db_module,
                "get_session",
                return_value=_mock_session(session),
            ),
            patch.object(
                handler_module.s3_module,
                "get_document_text",
                return_value=LONG_TRANSCRIPT,
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

        assert result == SAMPLE_RESULT


class TestScreeningEvalHandlerFailure:
    def test_short_transcript_sets_failed_status(self):
        import pytest

        from screening_eval import handler as handler_module

        evaluation = _make_mock_evaluation()
        document = _make_mock_document()
        candidate_position = _make_mock_candidate_position()
        position = _make_mock_position()
        session = _make_session_mock(evaluation, document, candidate_position, position)

        with (
            patch.object(
                handler_module.db_module,
                "get_session",
                return_value=_mock_session(session),
            ),
            patch.object(
                handler_module.s3_module,
                "get_document_text",
                return_value=SHORT_TRANSCRIPT,
            ),
            pytest.raises(ValueError, match="Transcript too short"),
        ):
            handler_module.handler({"detail": {"evaluation_id": 1}}, context=None)

        assert evaluation.status == "failed"
        assert "Transcript too short" in evaluation.error_message

    def test_short_transcript_never_calls_bedrock(self):
        import pytest

        from screening_eval import handler as handler_module

        evaluation = _make_mock_evaluation()
        document = _make_mock_document()
        candidate_position = _make_mock_candidate_position()
        position = _make_mock_position()
        session = _make_session_mock(evaluation, document, candidate_position, position)

        with (
            patch.object(
                handler_module.db_module,
                "get_session",
                return_value=_mock_session(session),
            ),
            patch.object(
                handler_module.s3_module,
                "get_document_text",
                return_value=SHORT_TRANSCRIPT,
            ),
            patch.object(
                handler_module.bedrock_module,
                "invoke_claude",
            ) as mock_bedrock,
            pytest.raises(ValueError),
        ):
            handler_module.handler({"detail": {"evaluation_id": 1}}, context=None)

        mock_bedrock.assert_not_called()

    def test_bedrock_error_sets_failed_status(self):
        import pytest

        from screening_eval import handler as handler_module

        evaluation = _make_mock_evaluation()
        document = _make_mock_document()
        candidate_position = _make_mock_candidate_position()
        position = _make_mock_position()
        session = _make_session_mock(evaluation, document, candidate_position, position)

        with (
            patch.object(
                handler_module.db_module,
                "get_session",
                return_value=_mock_session(session),
            ),
            patch.object(
                handler_module.s3_module,
                "get_document_text",
                return_value=LONG_TRANSCRIPT,
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

    def test_missing_result_sections_sets_failed_status(self):
        import pytest

        from screening_eval import handler as handler_module

        evaluation = _make_mock_evaluation()
        document = _make_mock_document()
        candidate_position = _make_mock_candidate_position()
        position = _make_mock_position()
        session = _make_session_mock(evaluation, document, candidate_position, position)

        incomplete_result = {
            "key_topics": ["topic"],
            "strengths": ["strength"],
        }

        with (
            patch.object(
                handler_module.db_module,
                "get_session",
                return_value=_mock_session(session),
            ),
            patch.object(
                handler_module.s3_module,
                "get_document_text",
                return_value=LONG_TRANSCRIPT,
            ),
            patch.object(
                handler_module.bedrock_module,
                "invoke_claude",
                return_value=json.dumps(incomplete_result),
            ),
            pytest.raises(ValueError, match="missing required sections"),
        ):
            handler_module.handler({"detail": {"evaluation_id": 1}}, context=None)

        assert evaluation.status == "failed"
