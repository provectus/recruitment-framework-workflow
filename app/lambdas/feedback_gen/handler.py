import json
import re
import sys
from datetime import UTC, datetime
from typing import Any

sys.path.insert(0, "/opt/python")
sys.path.insert(0, "/var/task")

from sqlalchemy import select

from shared import bedrock as bedrock_module
from shared import db as db_module
from shared.models import Evaluation
from shared.prompts.feedback_gen import build_feedback_gen_prompt


def _strip_markdown_fences(text: str) -> str:
    pattern = r"^```(?:json)?\s*\n?(.*?)\n?```\s*$"
    match = re.match(pattern, text.strip(), re.DOTALL)
    if match:
        return match.group(1).strip()
    return text.strip()


def _collect_completed_evaluations(session: Any, candidate_position_id: int) -> dict[str, Any]:
    relevant_step_types = ("cv_analysis", "screening_eval", "technical_eval")
    results: dict[str, Any] = {}

    for step_type in relevant_step_types:
        stmt = (
            select(Evaluation)
            .where(Evaluation.candidate_position_id == candidate_position_id)
            .where(Evaluation.step_type == step_type)
            .where(Evaluation.status == "completed")
            .order_by(Evaluation.version.desc())
            .limit(1)
        )
        row = session.execute(stmt).scalar_one_or_none()
        if row is not None and row.result:
            results[step_type] = row.result

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

            evaluation_results = _collect_completed_evaluations(
                session, evaluation.candidate_position_id
            )

            rejection_stage = _determine_rejection_stage(evaluation_results)

            system_prompt, user_prompt = build_feedback_gen_prompt(
                evaluation_results=evaluation_results,
                rejection_stage=rejection_stage,
            )

            raw_response = bedrock_module.invoke_claude(
                prompt=user_prompt,
                system_prompt=system_prompt,
                step_type="feedback_gen",
            )

            cleaned = _strip_markdown_fences(raw_response)
            result = json.loads(cleaned)

            if "feedback_text" not in result:
                raise ValueError("Bedrock response missing required field: feedback_text")

            result["rejection_stage"] = rejection_stage

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
