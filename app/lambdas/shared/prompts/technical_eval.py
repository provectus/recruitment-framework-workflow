from typing import Any

from shared.prompts.formatters import format_cv_analysis_result, format_screening_result

SYSTEM_PROMPT = """You score candidate technical interviews against a rubric. You assign scores based solely on evidence from the transcript, but use additional context (CV, position requirements, screening results) to provide deeper analysis.

Scoring scale:
1 — No evidence of competency
2 — Minimal / insufficient evidence
3 — Meets baseline expectations for a mid-level hire in this specific criterion
4 — Exceeds expectations with clear, strong demonstration
5 — Exceptional, expert-level demonstration with depth beyond what was asked

Calibration: anchor each score against the criterion's own description and weight. A "3" for system design requires different evidence than a "3" for communication — judge each against its specific competency definition.

Rules:
- Score every criterion listed, even if the transcript contains no relevant discussion (score 1).
- The evidence field must cite specific moments from the transcript.
- Keep reasoning to 2-3 sentences.
- Calculate weighted_total as: sum(score * weight) / sum(weight). We verify this server-side.
- cv_alignment: compare interview answers against CV claims and position requirements. Note confirmations, contradictions, and gaps.
- screening_consistency: if screening results are provided, note whether the technical interview confirms or contradicts screening signals. Write "N/A" if no screening data was available.
- skill_gaps: identify specific gaps between position requirements and demonstrated ability in the interview.
- follow_up_questions: suggest 2-4 targeted questions for a potential next interview round based on gaps or areas needing deeper exploration."""

TOOL_NAME = "technical_eval"

TOOL_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "thinking": {
            "type": "string",
            "description": "Your holistic reasoning about the candidate's technical performance across all criteria before scoring individual items. Consider patterns, relative strengths, and overall trajectory.",
        },
        "criteria_scores": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "criterion_name": {"type": "string"},
                    "category_name": {"type": "string"},
                    "score": {
                        "type": "integer",
                        "minimum": 1,
                        "maximum": 5,
                    },
                    "max_score": {"type": "integer", "const": 5},
                    "weight": {"type": "number"},
                    "evidence": {
                        "type": "string",
                        "description": "Direct quote or paraphrase from the transcript.",
                    },
                    "reasoning": {
                        "type": "string",
                        "description": "2-3 sentences explaining why this score was assigned.",
                    },
                },
                "required": [
                    "criterion_name",
                    "category_name",
                    "score",
                    "max_score",
                    "weight",
                    "evidence",
                    "reasoning",
                ],
            },
        },
        "weighted_total": {"type": "number"},
        "strengths_summary": {
            "type": "array",
            "items": {"type": "string"},
        },
        "improvement_areas": {
            "type": "array",
            "items": {"type": "string"},
        },
        "cv_alignment": {
            "type": "string",
            "description": "How interview answers align with or contradict CV claims and position requirements. Note confirmations, contradictions, and gaps.",
        },
        "screening_consistency": {
            "type": "string",
            "description": "Whether technical interview confirms or contradicts screening signals. 'N/A' if no screening data was available.",
        },
        "skill_gaps": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Specific gaps between position requirements and demonstrated ability.",
        },
        "follow_up_questions": {
            "type": "array",
            "items": {"type": "string"},
            "description": "2-4 targeted questions for a potential next interview round.",
        },
    },
    "required": [
        "thinking",
        "criteria_scores",
        "weighted_total",
        "strengths_summary",
        "improvement_areas",
        "cv_alignment",
        "screening_consistency",
        "skill_gaps",
        "follow_up_questions",
    ],
}


def _format_rubric_criteria(rubric_structure: dict[str, Any]) -> str:
    lines: list[str] = []
    for category in rubric_structure.get("categories", []):
        category_name = category.get("name", "Uncategorized")
        lines.append(f"### {category_name}")
        for criterion in category.get("criteria", []):
            name = criterion.get("name", "")
            weight = criterion.get("weight", 0)
            description = criterion.get("description", "")
            lines.append(f"- **{name}** (weight: {weight}): {description}")
        lines.append("")
    return "\n".join(lines).strip()


def _format_cv_context(
    cv_analysis_result: dict[str, Any] | None,
    cv_text: str | None,
) -> str:
    if cv_analysis_result is not None:
        return format_cv_analysis_result(
            cv_analysis_result,
            fields=("experience_relevance", "overall_fit"),
        )
    if cv_text is not None:
        return f"Raw CV Text:\n{cv_text}"
    return ""


def _format_screening_context(screening_result: dict[str, Any] | None) -> str:
    if screening_result is None:
        return ""
    return format_screening_result(screening_result, include_key_topics=False)


def build_technical_eval_prompt(
    position_title: str,
    position_description: str,
    rubric_structure: dict[str, Any],
    transcript_text: str,
    cv_analysis_result: dict[str, Any] | None = None,
    cv_text: str | None = None,
    screening_result: dict[str, Any] | None = None,
    evaluation_instructions: str = "",
) -> tuple[str, str]:
    formatted_criteria = _format_rubric_criteria(rubric_structure)

    context_sections: list[str] = []

    if evaluation_instructions:
        context_sections.append(f"## Evaluation Instructions\n\n{evaluation_instructions}")

    cv_context = _format_cv_context(cv_analysis_result, cv_text)
    if cv_context:
        context_sections.append(f"## Candidate Background\n\n{cv_context}")

    screening_context = _format_screening_context(screening_result)
    if screening_context:
        context_sections.append(f"## Prior Screening Signals\n\n{screening_context}")

    additional_context = ""
    if context_sections:
        additional_context = "\n\n---\n\n".join(context_sections) + "\n\n---\n\n"

    user_prompt = f"""Score the candidate interview transcript for the position described below using the rubric criteria provided.

## Position: {position_title}

### Description
{position_description}

---

{additional_context}## Evaluation Rubric

{formatted_criteria}

---

## Interview Transcript

{transcript_text}

---

Score every criterion from the rubric. For each, provide a score (1-5), the weight as listed, a direct evidence quote from the transcript, and your reasoning.

Additionally:
- Compare interview performance against the candidate's background (CV/prior analysis) and note alignments or contradictions.
- If screening signals are available, assess consistency with technical performance.
- Identify specific skill gaps relative to the position requirements.
- Suggest 2-4 follow-up questions for areas needing deeper exploration."""

    return SYSTEM_PROMPT, user_prompt
