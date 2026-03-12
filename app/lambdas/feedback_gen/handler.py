import logging
import sys
from typing import Any

sys.path.insert(0, "/opt/python")
sys.path.insert(0, "/var/task")

from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

from shared import bedrock as bedrock_module
from shared.evaluation_lifecycle import complete_evaluation, run_evaluation
from shared.prompts.feedback_gen import (
    TOOL_NAME,
    TOOL_SCHEMA,
    build_feedback_gen_prompt,
)
from shared.queries import fetch_latest_completed_result

_UPSTREAM_STEP_TYPES = ("cv_analysis", "screening_eval", "technical_eval")


def _collect_completed_evaluations(
    session: Session, candidate_position_id: int
) -> dict[str, Any]:
    results: dict[str, Any] = {}
    for step_type in _UPSTREAM_STEP_TYPES:
        result = fetch_latest_completed_result(
            session, candidate_position_id, step_type
        )
        if result is not None:
            results[step_type] = result
    return results


def _determine_rejection_stage(evaluation_results: dict[str, Any]) -> str:
    if "technical_eval" in evaluation_results:
        return "technical"
    if "screening_eval" in evaluation_results:
        return "screening"
    return "cv_review"


def handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    detail = event.get("detail", event)
    evaluation_id: int = detail["evaluation_id"]
    logger.info(
        "feedback_gen handler started", extra={"evaluation_id": evaluation_id}
    )

    with run_evaluation(evaluation_id) as (session, evaluation):
        evaluation_results = _collect_completed_evaluations(
            session, evaluation.candidate_position_id
        )

        rejection_stage = _determine_rejection_stage(evaluation_results)

        system_prompt, user_prompt = build_feedback_gen_prompt(
            evaluation_results=evaluation_results,
            rejection_stage=rejection_stage,
        )

        result = bedrock_module.invoke_claude_structured(
            prompt=user_prompt,
            tool_name=TOOL_NAME,
            tool_schema=TOOL_SCHEMA,
            system_prompt=system_prompt,
            step_type="feedback_gen",
        )

        if "feedback_text" not in result:
            raise ValueError(
                "Bedrock response missing required field: feedback_text"
            )

        result["rejection_stage"] = rejection_stage

        complete_evaluation(session, evaluation, result)
        logger.info(
            "feedback_gen handler completed",
            extra={"evaluation_id": evaluation_id},
        )
        return result
