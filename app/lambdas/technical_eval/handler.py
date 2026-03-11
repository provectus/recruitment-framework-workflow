import json
import sys
from datetime import UTC, datetime
from typing import Any

sys.path.insert(0, "/opt/python")
sys.path.insert(0, "/var/task")

from shared import bedrock as bedrock_module
from shared import db as db_module
from shared import s3 as s3_module
from shared.models import (
    CandidatePosition,
    Document,
    Evaluation,
    Position,
    PositionRubricVersion,
)
from shared.prompts.technical_eval import build_technical_eval_prompt
from shared.utils import strip_markdown_fences


def _calculate_weighted_total(criteria_scores: list[dict[str, Any]]) -> float:
    total_weight = sum(c.get("weight", 0) for c in criteria_scores)
    if total_weight == 0:
        return 0.0
    weighted_sum = sum(c.get("score", 0) * c.get("weight", 0) for c in criteria_scores)
    return round(weighted_sum / total_weight, 4)


def handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    detail = event.get("detail", event)
    evaluation_id: int = detail["evaluation_id"]

    with db_module.get_session() as session:
        evaluation = session.get(Evaluation, evaluation_id)
        if evaluation is None:
            raise ValueError(f"Evaluation {evaluation_id} not found")

        try:
            evaluation.status = "running"
            evaluation.started_at = datetime.now(tz=UTC)
            session.add(evaluation)
            session.commit()
            session.refresh(evaluation)

            if evaluation.source_document_id is None:
                raise ValueError(
                    f"Evaluation {evaluation_id} has no source_document_id"
                )

            if evaluation.rubric_version_id is None:
                raise ValueError("No rubric assigned")

            document = session.get(Document, evaluation.source_document_id)
            if document is None:
                raise ValueError(
                    f"Document {evaluation.source_document_id} not found"
                )

            candidate_position = session.get(
                CandidatePosition, evaluation.candidate_position_id
            )
            if candidate_position is None:
                raise ValueError(
                    f"CandidatePosition {evaluation.candidate_position_id} not found"
                )

            position = session.get(Position, candidate_position.position_id)
            if position is None:
                raise ValueError(
                    f"Position {candidate_position.position_id} not found"
                )

            rubric_version = session.get(
                PositionRubricVersion, evaluation.rubric_version_id
            )
            if rubric_version is None:
                raise ValueError(
                    f"PositionRubricVersion {evaluation.rubric_version_id} not found"
                )

            transcript_text = s3_module.get_document_text(document.s3_key)

            system_prompt, user_prompt = build_technical_eval_prompt(
                position_title=position.title,
                position_description=position.requirements or "",
                rubric_structure=rubric_version.structure,
                transcript_text=transcript_text,
            )

            raw_response = bedrock_module.invoke_claude(
                prompt=user_prompt,
                system_prompt=system_prompt,
                step_type="technical_eval",
            )

            cleaned = strip_markdown_fences(raw_response)
            result = json.loads(cleaned)

            result["weighted_total"] = _calculate_weighted_total(
                result.get("criteria_scores", [])
            )

            evaluation.status = "completed"
            evaluation.result = result
            evaluation.completed_at = datetime.now(tz=UTC)
            session.add(evaluation)
            session.commit()

            return result

        except Exception as exc:
            evaluation.status = "failed"
            evaluation.error_message = str(exc)
            evaluation.completed_at = datetime.now(tz=UTC)
            session.add(evaluation)
            session.commit()
            raise
