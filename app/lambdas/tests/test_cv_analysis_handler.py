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
    "skills_match": [
        {"skill": "Python", "present": True, "notes": "5 years experience"},
        {"skill": "FastAPI", "present": True, "notes": "Used in current role"},
    ],
    "experience_relevance": "Highly relevant backend experience.",
    "education": "BSc Computer Science.",
    "signals_and_red_flags": "Consistent career progression, no red flags.",
    "overall_fit": "Strong fit for the role.",
}


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
    doc.s3_key = "uploads/resume.pdf"
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


class TestCvAnalysisHandlerSuccess:
    def test_sets_evaluation_to_completed(self):
        from cv_analysis import handler as handler_module

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
                return_value="John Doe, 5 years Python",
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

    def test_sets_running_status_first(self):
        from cv_analysis import handler as handler_module

        evaluation = _make_mock_evaluation()
        document = _make_mock_document()
        candidate_position = _make_mock_candidate_position()
        position = _make_mock_position()
        session = _make_session_mock(evaluation, document, candidate_position, position)

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
                handler_module.s3_module,
                "get_document_text",
                return_value="CV text",
            ),
            patch.object(
                handler_module.bedrock_module,
                "invoke_claude",
                return_value=json.dumps(SAMPLE_RESULT),
            ),
        ):
            handler_module.handler({"detail": {"evaluation_id": 1}}, context=None)

        assert "running" in status_sequence
        running_idx = status_sequence.index("running")
        completed_idx = status_sequence.index("completed")
        assert running_idx < completed_idx

    def test_handles_markdown_wrapped_json(self):
        from cv_analysis import handler as handler_module

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
                return_value="CV text",
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

    def test_event_without_detail_wrapper(self):
        from cv_analysis import handler as handler_module

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
                return_value="CV text",
            ),
            patch.object(
                handler_module.bedrock_module,
                "invoke_claude",
                return_value=json.dumps(SAMPLE_RESULT),
            ),
        ):
            result = handler_module.handler({"evaluation_id": 1}, context=None)

        assert result == SAMPLE_RESULT


class TestCvAnalysisHandlerFailure:
    def test_sets_evaluation_to_failed_on_s3_error(self):
        import pytest

        from cv_analysis import handler as handler_module

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
                side_effect=FileNotFoundError("s3 key missing"),
            ),
            pytest.raises(FileNotFoundError),
        ):
            handler_module.handler({"detail": {"evaluation_id": 1}}, context=None)

        assert evaluation.status == "failed"
        assert "s3 key missing" in evaluation.error_message
        assert evaluation.completed_at is not None

    def test_sets_evaluation_to_failed_on_bedrock_error(self):
        import pytest

        from cv_analysis import handler as handler_module

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
                return_value="CV text",
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

    def test_commits_failure_before_reraising(self):
        import pytest

        from cv_analysis import handler as handler_module

        evaluation = _make_mock_evaluation()
        document = _make_mock_document()
        candidate_position = _make_mock_candidate_position()
        position = _make_mock_position()
        session = _make_session_mock(evaluation, document, candidate_position, position)

        commit_call_count: list[int] = [0]

        def counting_commit():
            commit_call_count[0] += 1

        session.commit.side_effect = counting_commit

        with (
            patch.object(
                handler_module.db_module,
                "get_session",
                return_value=_mock_session(session),
            ),
            patch.object(
                handler_module.s3_module,
                "get_document_text",
                side_effect=ValueError("unexpected"),
            ),
            pytest.raises(ValueError),
        ):
            handler_module.handler({"detail": {"evaluation_id": 1}}, context=None)

        assert commit_call_count[0] >= 2
