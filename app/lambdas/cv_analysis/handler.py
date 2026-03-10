import json
import re
import sys
from datetime import UTC, datetime
from typing import Any

sys.path.insert(0, "/opt/python")
sys.path.insert(0, "/var/task")

from shared import bedrock as bedrock_module
from shared import db as db_module
from shared import s3 as s3_module
from shared.models import CandidatePosition, Document, Evaluation, Position
from shared.prompts.cv_analysis import build_cv_analysis_prompt


def _strip_markdown_fences(text: str) -> str:
    pattern = r"^```(?:json)?\s*\n?(.*?)\n?```\s*$"
    match = re.match(pattern, text.strip(), re.DOTALL)
    if match:
        return match.group(1).strip()
    return text.strip()


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

            cv_text = s3_module.get_document_text(document.s3_key)
            required_skills = _extract_required_skills(position)

            system_prompt, user_prompt = build_cv_analysis_prompt(
                position_title=position.title,
                position_description=position.requirements or "",
                required_skills=required_skills,
                cv_text=cv_text,
            )

            raw_response = bedrock_module.invoke_claude(
                prompt=user_prompt,
                system_prompt=system_prompt,
                step_type="cv_analysis",
            )

            cleaned = _strip_markdown_fences(raw_response)
            result = json.loads(cleaned)

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
