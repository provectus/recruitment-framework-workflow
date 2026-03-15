import logging
import sys
from typing import Any

sys.path.insert(0, "/opt/python")
sys.path.insert(0, "/var/task")

from sqlalchemy import select
from sqlalchemy.orm import Session

from shared import bedrock as bedrock_module
from shared import s3 as s3_module
from shared.evaluation_lifecycle import complete_evaluation, run_evaluation
from shared.models import (
    CandidatePosition,
    Document,
    Position,
    PositionRubricVersion,
)
from shared.prompts.technical_eval import (
    TOOL_NAME,
    TOOL_SCHEMA,
    build_technical_eval_prompt,
)
from shared.queries import fetch_latest_completed_result

logger = logging.getLogger(__name__)


def _calculate_weighted_total(criteria_scores: list[dict[str, Any]]) -> float:
    total_weight = sum(c.get("weight", 0) for c in criteria_scores)
    if total_weight == 0:
        return 0.0
    weighted_sum = sum(c.get("score", 0) * c.get("weight", 0) for c in criteria_scores)
    return round(weighted_sum / total_weight, 4)


def _fetch_cv_context(
    session: Session,
    candidate_position_id: int,
) -> tuple[dict[str, Any] | None, str | None, str | None]:
    cv_analysis_result: dict[str, Any] | None = None
    cv_text: str | None = None
    errors: list[str] = []

    try:
        cv_analysis_result = fetch_latest_completed_result(
            session, candidate_position_id, "cv_analysis"
        )
    except Exception as exc:
        errors.append(f"cv_analysis query failed: {exc}")
        try:
            session.rollback()
        except Exception:
            pass

    if cv_analysis_result is None:
        try:
            stmt = (
                select(Document)
                .where(
                    Document.candidate_position_id == candidate_position_id,
                    Document.type == "cv",
                    Document.status == "uploaded",
                )
                .limit(1)
            )
            doc = session.execute(stmt).scalar_one_or_none()
            if doc is not None:
                cv_text = s3_module.get_document_text(doc.s3_key)
        except Exception as exc:
            errors.append(f"CV document fetch failed: {exc}")
            try:
                session.rollback()
            except Exception:
                pass

    error_msg = "; ".join(errors) if errors else None
    return cv_analysis_result, cv_text, error_msg


def _fetch_screening_result(
    session: Session,
    candidate_position_id: int,
) -> tuple[dict[str, Any] | None, str | None]:
    try:
        result = fetch_latest_completed_result(
            session, candidate_position_id, "screening_eval"
        )
        return result, None
    except Exception as exc:
        try:
            session.rollback()
        except Exception:
            pass
        return None, f"screening_eval query failed: {exc}"


def handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    detail = event.get("detail", event)
    evaluation_id: int = detail["evaluation_id"]

    with run_evaluation(evaluation_id) as (session, evaluation):
        if evaluation.source_document_id is None:
            raise ValueError(f"Evaluation {evaluation_id} has no source_document_id")

        if evaluation.rubric_version_id is None:
            raise ValueError("No rubric assigned")

        document = session.get(Document, evaluation.source_document_id)
        if document is None:
            raise ValueError(f"Document {evaluation.source_document_id} not found")

        candidate_position = session.get(
            CandidatePosition, evaluation.candidate_position_id
        )
        if candidate_position is None:
            raise ValueError(
                f"CandidatePosition {evaluation.candidate_position_id} not found"
            )

        position = session.get(Position, candidate_position.position_id)
        if position is None:
            raise ValueError(f"Position {candidate_position.position_id} not found")

        rubric_version = session.get(
            PositionRubricVersion, evaluation.rubric_version_id
        )
        if rubric_version is None:
            raise ValueError(
                f"PositionRubricVersion {evaluation.rubric_version_id} not found"
            )

        cv_analysis_result, cv_text, cv_error = _fetch_cv_context(
            session, evaluation.candidate_position_id
        )
        if cv_error:
            logger.error("CV context fetch failed: %s", cv_error)

        screening_result, screening_error = _fetch_screening_result(
            session, evaluation.candidate_position_id
        )
        if screening_error:
            logger.error("Screening result fetch failed: %s", screening_error)

        transcript_text = s3_module.get_document_text(document.s3_key)

        system_prompt, user_prompt = build_technical_eval_prompt(
            position_title=position.title,
            position_description=position.requirements or "",
            rubric_structure=rubric_version.structure,
            transcript_text=transcript_text,
            cv_analysis_result=cv_analysis_result,
            cv_text=cv_text,
            screening_result=screening_result,
            evaluation_instructions=position.evaluation_instructions or "",
        )

        result = bedrock_module.invoke_claude_structured(
            prompt=user_prompt,
            tool_name=TOOL_NAME,
            tool_schema=TOOL_SCHEMA,
            system_prompt=system_prompt,
            step_type="technical_eval",
        )

        result["weighted_total"] = _calculate_weighted_total(
            result.get("criteria_scores", [])
        )

        complete_evaluation(session, evaluation, result)
        return result
