import os
from contextlib import contextmanager
from typing import Any
from unittest.mock import MagicMock, patch

os.environ.setdefault("DB_HOST", "localhost")
os.environ.setdefault("DB_NAME", "test")
os.environ.setdefault("DB_USERNAME", "test")
os.environ.setdefault("DB_PASSWORD", "test")
os.environ.setdefault("S3_BUCKET_NAME", "test-bucket")
os.environ.setdefault("BEDROCK_MODEL_ID", "anthropic.claude-sonnet-4-6")
os.environ.setdefault("AWS_REGION", "us-east-1")

SAMPLE_RUBRIC_STRUCTURE = {
    "categories": [
        {
            "name": "Technical Skills",
            "criteria": [
                {
                    "name": "System Design",
                    "weight": 0.3,
                    "description": "Ability to design scalable systems",
                },
                {
                    "name": "Coding",
                    "weight": 0.2,
                    "description": "Code quality and problem solving",
                },
            ],
        },
        {
            "name": "Soft Skills",
            "criteria": [
                {
                    "name": "Communication",
                    "weight": 0.5,
                    "description": "Clarity and structure of answers",
                },
            ],
        },
    ]
}

SAMPLE_CV_ANALYSIS_RESULT: dict[str, Any] = {
    "skills_match": [
        {"skill": "Python", "present": True, "notes": "5 years experience."},
        {"skill": "AWS", "present": True, "notes": "EC2, S3, Lambda."},
        {"skill": "TypeScript", "present": False, "notes": "Not mentioned."},
    ],
    "experience_relevance": "6 years backend engineering.",
    "overall_fit": "Strong technical match.",
}

SAMPLE_SCREENING_RESULT: dict[str, Any] = {
    "strengths": ["Well-prepared", "Concrete examples"],
    "concerns": ["Salary expectations above range"],
    "communication_quality": "Clear and professional.",
    "motivation_culture_fit": "Genuine interest in company mission.",
}

SAMPLE_LLM_RESULT: dict[str, Any] = {
    "criteria_scores": [
        {
            "criterion_name": "System Design",
            "category_name": "Technical Skills",
            "score": 4,
            "max_score": 5,
            "weight": 0.3,
            "evidence": "Candidate described a microservices approach with event sourcing.",
            "reasoning": "Clear architectural thinking with appropriate trade-off awareness.",
        },
        {
            "criterion_name": "Coding",
            "category_name": "Technical Skills",
            "score": 3,
            "max_score": 5,
            "weight": 0.2,
            "evidence": "Wrote a working BFS solution with minor inefficiency.",
            "reasoning": "Correct solution but missed the O(n) optimization opportunity.",
        },
        {
            "criterion_name": "Communication",
            "category_name": "Soft Skills",
            "score": 5,
            "max_score": 5,
            "weight": 0.5,
            "evidence": "Explained each concept clearly with structured answers.",
            "reasoning": "Exceptionally clear communicator throughout the interview.",
        },
    ],
    "weighted_total": 99.9,
    "strengths_summary": ["Strong system design instincts", "Excellent communication"],
    "improvement_areas": ["Coding optimization"],
    "cv_alignment": "Interview confirms CV claims about Python experience.",
    "screening_consistency": "Consistent with screening signals.",
    "skill_gaps": ["Distributed systems consistency patterns"],
    "follow_up_questions": ["Describe your experience with eventual consistency."],
}


def _make_mock_evaluation(
    evaluation_id: int = 1,
    rubric_version_id: int | None = 7,
) -> MagicMock:
    evaluation = MagicMock()
    evaluation.id = evaluation_id
    evaluation.status = "pending"
    evaluation.source_document_id = 10
    evaluation.candidate_position_id = 5
    evaluation.rubric_version_id = rubric_version_id
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
    pos.requirements = "Design scalable backend systems"
    return pos


def _make_mock_rubric_version(rubric_version_id: int = 7) -> MagicMock:
    rv = MagicMock()
    rv.id = rubric_version_id
    rv.structure = SAMPLE_RUBRIC_STRUCTURE
    return rv


def _make_mock_cv_analysis_evaluation(
    result: dict[str, Any] | None = None,
) -> MagicMock:
    ev = MagicMock()
    ev.step_type = "cv_analysis"
    ev.status = "completed"
    ev.result = result if result is not None else SAMPLE_CV_ANALYSIS_RESULT
    return ev


def _make_mock_screening_evaluation(
    result: dict[str, Any] | None = None,
) -> MagicMock:
    ev = MagicMock()
    ev.step_type = "screening_eval"
    ev.status = "completed"
    ev.result = result if result is not None else SAMPLE_SCREENING_RESULT
    return ev


def _make_session_mock(
    evaluation: MagicMock,
    document: MagicMock,
    candidate_position: MagicMock,
    position: MagicMock,
    rubric_version: MagicMock | None = None,
    cv_analysis_eval: MagicMock | None = None,
    screening_eval: MagicMock | None = None,
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
        if model_class.__name__ == "PositionRubricVersion":
            return rubric_version
        return None

    execute_results = iter([cv_analysis_eval, screening_eval])

    def session_execute(stmt):
        row = next(execute_results, None)
        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = row
        return result_mock

    session.get.side_effect = session_get
    session.execute.side_effect = session_execute
    return session


@contextmanager
def _mock_session(session: MagicMock):
    yield session


class TestTechnicalEvalHandlerSuccess:
    def test_server_calculates_weighted_total(self):
        from technical_eval import handler as handler_module

        evaluation = _make_mock_evaluation()
        document = _make_mock_document()
        candidate_position = _make_mock_candidate_position()
        position = _make_mock_position()
        rubric_version = _make_mock_rubric_version()
        session = _make_session_mock(
            evaluation, document, candidate_position, position, rubric_version
        )

        with (
            patch(
                "shared.db.get_session",
                return_value=_mock_session(session),
            ),
            patch.object(
                handler_module.s3_module,
                "get_document_text",
                return_value="Transcript text here.",
            ),
            patch.object(
                handler_module.bedrock_module,
                "invoke_claude_structured",
                return_value=SAMPLE_LLM_RESULT,
            ),
        ):
            result = handler_module.handler(
                {"detail": {"evaluation_id": 1}}, context=None
            )

        # LLM returned 99.9 but server should override:
        # (4*0.3 + 3*0.2 + 5*0.5) / (0.3 + 0.2 + 0.5) = (1.2 + 0.6 + 2.5) / 1.0 = 4.3
        assert result["weighted_total"] == 4.3
        assert result["weighted_total"] != 99.9

    def test_weighted_total_two_criteria(self):
        from technical_eval import handler as handler_module

        llm_result = {
            "criteria_scores": [
                {
                    "criterion_name": "System Design",
                    "category_name": "Technical Skills",
                    "score": 4,
                    "max_score": 5,
                    "weight": 0.3,
                    "evidence": "...",
                    "reasoning": "...",
                },
                {
                    "criterion_name": "Coding",
                    "category_name": "Technical Skills",
                    "score": 3,
                    "max_score": 5,
                    "weight": 0.2,
                    "evidence": "...",
                    "reasoning": "...",
                },
            ],
            "weighted_total": 0.0,
            "strengths_summary": [],
            "improvement_areas": [],
        }

        evaluation = _make_mock_evaluation()
        document = _make_mock_document()
        candidate_position = _make_mock_candidate_position()
        position = _make_mock_position()
        rubric_version = _make_mock_rubric_version()
        session = _make_session_mock(
            evaluation, document, candidate_position, position, rubric_version
        )

        with (
            patch(
                "shared.db.get_session",
                return_value=_mock_session(session),
            ),
            patch.object(
                handler_module.s3_module,
                "get_document_text",
                return_value="Transcript.",
            ),
            patch.object(
                handler_module.bedrock_module,
                "invoke_claude_structured",
                return_value=llm_result,
            ),
        ):
            result = handler_module.handler(
                {"detail": {"evaluation_id": 1}}, context=None
            )

        # (4*0.3 + 3*0.2) / (0.3 + 0.2) = (1.2 + 0.6) / 0.5 = 3.6
        assert result["weighted_total"] == 3.6

    def test_sets_evaluation_to_completed_with_all_scores(self):
        from technical_eval import handler as handler_module

        evaluation = _make_mock_evaluation()
        document = _make_mock_document()
        candidate_position = _make_mock_candidate_position()
        position = _make_mock_position()
        rubric_version = _make_mock_rubric_version()
        session = _make_session_mock(
            evaluation, document, candidate_position, position, rubric_version
        )

        with (
            patch(
                "shared.db.get_session",
                return_value=_mock_session(session),
            ),
            patch.object(
                handler_module.s3_module,
                "get_document_text",
                return_value="Interview transcript.",
            ),
            patch.object(
                handler_module.bedrock_module,
                "invoke_claude_structured",
                return_value=SAMPLE_LLM_RESULT,
            ),
        ):
            result = handler_module.handler(
                {"detail": {"evaluation_id": 1}}, context=None
            )

        assert evaluation.status == "completed"
        assert evaluation.completed_at is not None
        assert len(result["criteria_scores"]) == 3
        assert "strengths_summary" in result
        assert "improvement_areas" in result

    def test_sets_running_status_before_completed(self):
        from technical_eval import handler as handler_module

        evaluation = _make_mock_evaluation()
        document = _make_mock_document()
        candidate_position = _make_mock_candidate_position()
        position = _make_mock_position()
        rubric_version = _make_mock_rubric_version()
        session = _make_session_mock(
            evaluation, document, candidate_position, position, rubric_version
        )

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
                handler_module.s3_module,
                "get_document_text",
                return_value="Transcript.",
            ),
            patch.object(
                handler_module.bedrock_module,
                "invoke_claude_structured",
                return_value=SAMPLE_LLM_RESULT,
            ),
        ):
            handler_module.handler({"detail": {"evaluation_id": 1}}, context=None)

        assert "running" in status_sequence
        assert status_sequence.index("running") < status_sequence.index("completed")


class TestTechnicalEvalHandlerFailure:
    def test_missing_rubric_version_id_fails_with_message(self):
        import pytest

        from technical_eval import handler as handler_module

        evaluation = _make_mock_evaluation(rubric_version_id=None)
        document = _make_mock_document()
        candidate_position = _make_mock_candidate_position()
        position = _make_mock_position()
        session = _make_session_mock(
            evaluation, document, candidate_position, position, rubric_version=None
        )

        with (
            patch(
                "shared.db.get_session",
                return_value=_mock_session(session),
            ),
            pytest.raises(ValueError, match="No rubric assigned"),
        ):
            handler_module.handler({"detail": {"evaluation_id": 1}}, context=None)

        assert evaluation.status == "failed"
        assert "No rubric assigned" in evaluation.error_message

    def test_sets_failed_on_s3_error(self):
        import pytest

        from technical_eval import handler as handler_module

        evaluation = _make_mock_evaluation()
        document = _make_mock_document()
        candidate_position = _make_mock_candidate_position()
        position = _make_mock_position()
        rubric_version = _make_mock_rubric_version()
        session = _make_session_mock(
            evaluation, document, candidate_position, position, rubric_version
        )

        with (
            patch(
                "shared.db.get_session",
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

    def test_sets_failed_on_bedrock_error(self):
        import pytest

        from technical_eval import handler as handler_module

        evaluation = _make_mock_evaluation()
        document = _make_mock_document()
        candidate_position = _make_mock_candidate_position()
        position = _make_mock_position()
        rubric_version = _make_mock_rubric_version()
        session = _make_session_mock(
            evaluation, document, candidate_position, position, rubric_version
        )

        with (
            patch(
                "shared.db.get_session",
                return_value=_mock_session(session),
            ),
            patch.object(
                handler_module.s3_module,
                "get_document_text",
                return_value="Transcript.",
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


class TestTechnicalEvalContextEnrichment:
    def test_screening_data_included_in_prompt(self):
        from technical_eval import handler as handler_module

        evaluation = _make_mock_evaluation()
        document = _make_mock_document()
        candidate_position = _make_mock_candidate_position()
        position = _make_mock_position()
        rubric_version = _make_mock_rubric_version()
        cv_eval = _make_mock_cv_analysis_evaluation()
        screening_eval = _make_mock_screening_evaluation()
        session = _make_session_mock(
            evaluation,
            document,
            candidate_position,
            position,
            rubric_version,
            cv_analysis_eval=cv_eval,
            screening_eval=screening_eval,
        )

        captured_prompt = {}

        def capture_bedrock_call(**kwargs):
            captured_prompt["user_prompt"] = kwargs.get("prompt", "")
            return SAMPLE_LLM_RESULT

        with (
            patch(
                "shared.db.get_session",
                return_value=_mock_session(session),
            ),
            patch.object(
                handler_module.s3_module,
                "get_document_text",
                return_value="Transcript.",
            ),
            patch.object(
                handler_module.bedrock_module,
                "invoke_claude_structured",
                side_effect=capture_bedrock_call,
            ),
        ):
            handler_module.handler({"detail": {"evaluation_id": 1}}, context=None)

        prompt = captured_prompt["user_prompt"]
        assert "Candidate Background" in prompt
        assert "CV Analysis Results:" in prompt
        assert "Python" in prompt
        assert "Prior Screening Signals" in prompt
        assert "Screening Interview Results:" in prompt
        assert "Well-prepared" in prompt

    def test_screening_absent_handler_proceeds(self):
        from technical_eval import handler as handler_module

        evaluation = _make_mock_evaluation()
        document = _make_mock_document()
        candidate_position = _make_mock_candidate_position()
        position = _make_mock_position()
        rubric_version = _make_mock_rubric_version()
        cv_eval = _make_mock_cv_analysis_evaluation()
        session = _make_session_mock(
            evaluation,
            document,
            candidate_position,
            position,
            rubric_version,
            cv_analysis_eval=cv_eval,
            screening_eval=None,
        )

        captured_prompt = {}

        def capture_bedrock_call(**kwargs):
            captured_prompt["user_prompt"] = kwargs.get("prompt", "")
            return SAMPLE_LLM_RESULT

        with (
            patch(
                "shared.db.get_session",
                return_value=_mock_session(session),
            ),
            patch.object(
                handler_module.s3_module,
                "get_document_text",
                return_value="Transcript.",
            ),
            patch.object(
                handler_module.bedrock_module,
                "invoke_claude_structured",
                side_effect=capture_bedrock_call,
            ),
        ):
            result = handler_module.handler(
                {"detail": {"evaluation_id": 1}}, context=None
            )

        assert evaluation.status == "completed"
        prompt = captured_prompt["user_prompt"]
        assert "Prior Screening Signals" not in prompt
        assert "screening_consistency" in result

    def test_cv_fetch_failure_proceeds_gracefully(self):
        from technical_eval import handler as handler_module

        evaluation = _make_mock_evaluation()
        document = _make_mock_document()
        candidate_position = _make_mock_candidate_position()
        position = _make_mock_position()
        rubric_version = _make_mock_rubric_version()

        session = _make_session_mock(
            evaluation, document, candidate_position, position, rubric_version
        )
        session.execute.side_effect = RuntimeError("DB connection lost")

        with (
            patch(
                "shared.db.get_session",
                return_value=_mock_session(session),
            ),
            patch.object(
                handler_module.s3_module,
                "get_document_text",
                return_value="Transcript.",
            ),
            patch.object(
                handler_module.bedrock_module,
                "invoke_claude_structured",
                return_value=SAMPLE_LLM_RESULT,
            ),
        ):
            result = handler_module.handler(
                {"detail": {"evaluation_id": 1}}, context=None
            )

        assert evaluation.status == "completed"
        assert "weighted_total" in result

    def test_no_context_produces_minimal_prompt(self):
        from technical_eval import handler as handler_module

        evaluation = _make_mock_evaluation()
        document = _make_mock_document()
        candidate_position = _make_mock_candidate_position()
        position = _make_mock_position()
        rubric_version = _make_mock_rubric_version()
        session = _make_session_mock(
            evaluation,
            document,
            candidate_position,
            position,
            rubric_version,
            cv_analysis_eval=None,
            screening_eval=None,
        )

        captured_prompt = {}

        def capture_bedrock_call(**kwargs):
            captured_prompt["user_prompt"] = kwargs.get("prompt", "")
            return SAMPLE_LLM_RESULT

        with (
            patch(
                "shared.db.get_session",
                return_value=_mock_session(session),
            ),
            patch.object(
                handler_module.s3_module,
                "get_document_text",
                return_value="Transcript.",
            ),
            patch.object(
                handler_module.bedrock_module,
                "invoke_claude_structured",
                side_effect=capture_bedrock_call,
            ),
        ):
            handler_module.handler({"detail": {"evaluation_id": 1}}, context=None)

        prompt = captured_prompt["user_prompt"]
        assert "Candidate Background" not in prompt
        assert "Prior Screening Signals" not in prompt
        assert "Evaluation Rubric" in prompt
        assert "Interview Transcript" in prompt
