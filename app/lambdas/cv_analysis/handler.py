import logging
import sys
from typing import Any

sys.path.insert(0, "/opt/python")
sys.path.insert(0, "/var/task")

from shared import bedrock as bedrock_module
from shared import s3 as s3_module
from shared.evaluation_lifecycle import complete_evaluation, run_evaluation
from shared.models import CandidatePosition, Document, Position
from shared.prompts.cv_analysis import TOOL_NAME, TOOL_SCHEMA, build_cv_analysis_prompt

logger = logging.getLogger(__name__)


def _extract_required_skills(position: Position) -> list[str]:
    if not position.requirements:
        return []
    lines = position.requirements.splitlines()
    skills = []
    for line in lines:
        stripped = line.strip().lstrip("-*•").strip()
        if stripped:
            skills.append(stripped)
    return skills


def handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    detail = event.get("detail", event)
    evaluation_id: int = detail["evaluation_id"]
    logger.info("cv_analysis handler started", extra={"evaluation_id": evaluation_id})

    with run_evaluation(evaluation_id) as (session, evaluation):
        if evaluation.source_document_id is None:
            raise ValueError(f"Evaluation {evaluation_id} has no source_document_id")

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

        cv_text = s3_module.get_document_text(document.s3_key)
        required_skills = _extract_required_skills(position)

        system_prompt, user_prompt = build_cv_analysis_prompt(
            position_title=position.title,
            position_description=position.requirements or "",
            required_skills=required_skills,
            cv_text=cv_text,
            evaluation_instructions=position.evaluation_instructions or "",
        )

        result = bedrock_module.invoke_claude_structured(
            prompt=user_prompt,
            tool_name=TOOL_NAME,
            tool_schema=TOOL_SCHEMA,
            system_prompt=system_prompt,
            step_type="cv_analysis",
        )

        complete_evaluation(session, evaluation, result)
        logger.info(
            "cv_analysis handler completed", extra={"evaluation_id": evaluation_id}
        )
        return result
