from typing import Any

from shared.prompts.formatters import format_cv_analysis_result, format_screening_result

SYSTEM_PROMPT = """You synthesize evidence from multiple recruitment evaluation stages and produce a clear, reasoned hiring recommendation.

Field definitions:
- recommendation: "hire" (strong fit, move forward), "no_hire" (not a good fit), or "needs_discussion" (mixed/insufficient evidence requiring human judgment)
- confidence: "high" (all inputs available, evidence clear and consistent), "medium" (all inputs available but evidence mixed), "low" (one or more inputs missing OR evidence contradictory)
- reasoning: 3-5 sentence narrative citing specific findings from the available evaluation steps
- missing_inputs: list of step names that were NOT AVAILABLE (empty list if all present)

Rules:
- Base your recommendation only on evidence present in the provided evaluation results.
- When inputs are missing, acknowledge the gap explicitly in your reasoning.
- Do not invent information not present in the provided evaluations.
- The missing_inputs field must accurately list every step marked "NOT AVAILABLE"."""

TOOL_NAME = "recommendation"

TOOL_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "thinking": {
            "type": "string",
            "description": "Your internal reasoning synthesizing all available evidence before making the recommendation. Weigh strengths against concerns, note any gaps, and explain your confidence calibration.",
        },
        "recommendation": {
            "type": "string",
            "enum": ["hire", "no_hire", "needs_discussion"],
        },
        "confidence": {
            "type": "string",
            "enum": ["high", "medium", "low"],
        },
        "reasoning": {
            "type": "string",
            "description": "3-5 sentence narrative referencing specific evidence from prior evaluation steps.",
        },
        "missing_inputs": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Step names that were NOT AVAILABLE (e.g. 'cv_analysis'). Empty list if all present.",
        },
    },
    "required": [
        "thinking",
        "recommendation",
        "confidence",
        "reasoning",
        "missing_inputs",
    ],
}


def _format_cv_analysis(result: dict[str, Any] | None) -> str:
    if result is None:
        return "NOT AVAILABLE - this evaluation step was not completed or failed"
    return format_cv_analysis_result(result)


def _format_screening_eval(result: dict[str, Any] | None) -> str:
    if result is None:
        return "NOT AVAILABLE - this evaluation step was not completed or failed"
    return format_screening_result(result)


def _format_technical_eval(result: dict[str, Any] | None) -> str:
    if result is None:
        return "NOT AVAILABLE - this evaluation step was not completed or failed"

    lines = ["Technical Interview Results:"]

    weighted_total = result.get("weighted_total")
    if weighted_total is not None:
        lines.append(f"  Weighted score: {weighted_total}")

    criteria_scores = result.get("criteria_scores", [])
    if criteria_scores:
        scored = [
            f"{c.get('criterion_name', 'Unknown')} ({c.get('score', '?')}/{c.get('max_score', 5)})"
            for c in criteria_scores
        ]
        lines.append(f"  Criteria scores: {', '.join(scored)}")

    strengths_summary = result.get("strengths_summary", [])
    if strengths_summary:
        lines.append(f"  Strengths: {'; '.join(strengths_summary)}")

    improvement_areas = result.get("improvement_areas", [])
    if improvement_areas:
        lines.append(f"  Improvement areas: {'; '.join(improvement_areas)}")

    return "\n".join(lines)


def build_recommendation_prompt(
    cv_analysis_result: dict[str, Any] | None,
    screening_eval_result: dict[str, Any] | None,
    technical_eval_result: dict[str, Any] | None,
    position_title: str,
    position_description: str,
    evaluation_instructions: str = "",
) -> tuple[str, str]:
    cv_section = _format_cv_analysis(cv_analysis_result)
    screening_section = _format_screening_eval(screening_eval_result)
    technical_section = _format_technical_eval(technical_eval_result)

    missing = []
    if cv_analysis_result is None:
        missing.append("cv_analysis")
    if screening_eval_result is None:
        missing.append("screening_eval")
    if technical_eval_result is None:
        missing.append("technical_eval")

    confidence_note = (
        "\nIMPORTANT: One or more evaluation inputs are missing (marked NOT AVAILABLE). "
        "You MUST set confidence to \"low\" — this is non-negotiable."
        if missing
        else ""
    )

    instructions_section = ""
    if evaluation_instructions:
        instructions_section = f"""
## Evaluation Instructions

{evaluation_instructions}

---
"""

    user_prompt = f"""Synthesize the evaluation results below and produce a final hiring recommendation for the position.

## Position: {position_title}

### Requirements
{position_description}

---
{instructions_section}
## Evaluation Results

### 1. CV Analysis

{cv_section}

### 2. Screening Interview

{screening_section}

### 3. Technical Interview

{technical_section}

---
{confidence_note}"""

    return SYSTEM_PROMPT, user_prompt
