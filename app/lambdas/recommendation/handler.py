import json
import sys
from datetime import UTC, datetime
from typing import Any

sys.path.insert(0, "/opt/python")
sys.path.insert(0, "/var/task")

from sqlalchemy import select

from shared import bedrock as bedrock_module
from shared import db as db_module
from shared.models import CandidatePosition, Evaluation, Position
from shared.prompts.recommendation import build_recommendation_prompt
from shared.utils import strip_markdown_fences

VALID_RECOMMENDATIONS = {"hire", "no_hire", "needs_discussion"}
VALID_CONFIDENCE_LEVELS = {"high", "medium", "low"}
UPSTREAM_STEP_TYPES = ("cv_analysis", "screening_eval", "technical_eval")


def _fetch_latest_completed_results(
    session: Any, candidate_position_id: int
) -> dict[str, dict[str, Any] | None]:
    results: dict[str, dict[str, Any] | None] = dict.fromkeys(UPSTREAM_STEP_TYPES)

    for step_type in UPSTREAM_STEP_TYPES:
        stmt = (
            select(Evaluation)
            .where(
                Evaluation.candidate_position_id == candidate_position_id,
                Evaluation.step_type == step_type,
                Evaluation.status == "completed",
            )
            .order_by(Evaluation.version.desc())
            .limit(1)
        )
        row = session.execute(stmt).scalar_one_or_none()
        if row is not None:
            results[step_type] = row.result

    return results


def _validate_and_fix_result(
    result: dict[str, Any],
    missing_step_types: list[str],
) -> dict[str, Any]:
    if result.get("recommendation") not in VALID_RECOMMENDATIONS:
        result["recommendation"] = "needs_discussion"

    if result.get("confidence") not in VALID_CONFIDENCE_LEVELS:
        result["confidence"] = "low"

    if missing_step_types:
        result["confidence"] = "low"

    if "missing_inputs" not in result or not isinstance(result["missing_inputs"], list):
        result["missing_inputs"] = missing_step_types
    elif missing_step_types:
        for step in missing_step_types:
            if step not in result["missing_inputs"]:
                result["missing_inputs"].append(step)

    if "reasoning" not in result or not result.get("reasoning"):
        result["reasoning"] = "Recommendation produced without detailed reasoning."

    return result


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

            upstream_results = _fetch_latest_completed_results(
                session, evaluation.candidate_position_id
            )

            missing_step_types = [
                step for step, result in upstream_results.items() if result is None
            ]

            system_prompt, user_prompt = build_recommendation_prompt(
                cv_analysis_result=upstream_results["cv_analysis"],
                screening_eval_result=upstream_results["screening_eval"],
                technical_eval_result=upstream_results["technical_eval"],
                position_title=position.title,
                position_description=position.requirements or "",
            )

            raw_response = bedrock_module.invoke_claude(
                prompt=user_prompt,
                system_prompt=system_prompt,
                step_type="recommendation",
            )

            cleaned = strip_markdown_fences(raw_response)
            result = json.loads(cleaned)

            result = _validate_and_fix_result(result, missing_step_types)

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
