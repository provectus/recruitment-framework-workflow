import logging
import sys
from typing import Any

sys.path.insert(0, "/opt/python")
sys.path.insert(0, "/var/task")

from shared import bedrock as bedrock_module
from shared import s3 as s3_module
from shared.evaluation_lifecycle import complete_evaluation, run_evaluation
from shared.models import CandidatePosition, Document, Position
from shared.prompts.screening_eval import (
    TOOL_NAME,
    TOOL_SCHEMA,
    build_screening_eval_prompt,
)

logger = logging.getLogger(__name__)

REQUIRED_RESULT_SECTIONS = {
    "key_topics",
    "strengths",
    "concerns",
    "communication_quality",
    "motivation_culture_fit",
    "requirements_alignment",
}

MIN_TRANSCRIPT_WORDS = 100


def _validate_transcript_length(text: str) -> None:
    word_count = len(text.split())
    if word_count < MIN_TRANSCRIPT_WORDS:
        raise ValueError(
            f"Transcript too short for meaningful analysis "
            f"({word_count} words, minimum {MIN_TRANSCRIPT_WORDS})"
        )


def _validate_result_sections(result: dict[str, Any]) -> None:
    missing = REQUIRED_RESULT_SECTIONS - result.keys()
    if missing:
        raise ValueError(
            f"Bedrock response missing required sections: {sorted(missing)}"
        )


def handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    detail = event.get("detail", event)
    evaluation_id: int = detail["evaluation_id"]
    logger.info(
        "screening_eval handler started", extra={"evaluation_id": evaluation_id}
    )

    with run_evaluation(evaluation_id) as (session, evaluation):
        if evaluation.source_document_id is None:
            raise ValueError(
                f"Evaluation {evaluation_id} has no source_document_id"
            )

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

        transcript_text = s3_module.get_document_text(document.s3_key)
        _validate_transcript_length(transcript_text)

        system_prompt, user_prompt = build_screening_eval_prompt(
            position_title=position.title,
            position_description=position.requirements or "",
            transcript_text=transcript_text,
            evaluation_instructions=position.evaluation_instructions or "",
        )

        result = bedrock_module.invoke_claude_structured(
            prompt=user_prompt,
            tool_name=TOOL_NAME,
            tool_schema=TOOL_SCHEMA,
            system_prompt=system_prompt,
            step_type="screening_eval",
        )
        _validate_result_sections(result)

        complete_evaluation(session, evaluation, result)
        logger.info(
            "screening_eval handler completed",
            extra={"evaluation_id": evaluation_id},
        )
        return result
