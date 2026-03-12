import logging
import sys
from typing import Any

sys.path.insert(0, "/opt/python")
sys.path.insert(0, "/var/task")

from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

from shared import bedrock as bedrock_module
from shared.evaluation_lifecycle import complete_evaluation, run_evaluation
from shared.models import CandidatePosition, Position
from shared.prompts.recommendation import (
    TOOL_NAME,
    TOOL_SCHEMA,
    build_recommendation_prompt,
)
from shared.queries import fetch_latest_completed_result

VALID_RECOMMENDATIONS = {"hire", "no_hire", "needs_discussion"}
VALID_CONFIDENCE_LEVELS = {"high", "medium", "low"}
UPSTREAM_STEP_TYPES = ("cv_analysis", "screening_eval", "technical_eval")


def _fetch_latest_completed_results(
    session: Session, candidate_position_id: int
) -> dict[str, dict[str, Any] | None]:
    results: dict[str, dict[str, Any] | None] = dict.fromkeys(UPSTREAM_STEP_TYPES)

    for step_type in UPSTREAM_STEP_TYPES:
        results[step_type] = fetch_latest_completed_result(
            session, candidate_position_id, step_type
        )

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
    logger.info(
        "recommendation handler started", extra={"evaluation_id": evaluation_id}
    )

    with run_evaluation(evaluation_id) as (session, evaluation):
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
            evaluation_instructions=position.evaluation_instructions or "",
        )

        result = bedrock_module.invoke_claude_structured(
            prompt=user_prompt,
            tool_name=TOOL_NAME,
            tool_schema=TOOL_SCHEMA,
            system_prompt=system_prompt,
            step_type="recommendation",
        )

        result = _validate_and_fix_result(result, missing_step_types)

        complete_evaluation(session, evaluation, result)
        logger.info(
            "recommendation handler completed",
            extra={"evaluation_id": evaluation_id},
        )
        return result
