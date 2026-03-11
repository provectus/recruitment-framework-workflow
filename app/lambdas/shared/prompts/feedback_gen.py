from typing import Any

SYSTEM_PROMPT = """You are a compassionate and professional talent acquisition specialist drafting a rejection feedback letter on behalf of a company.

Your task is to write constructive, personalized feedback for a candidate who was not selected for a position. The feedback must be honest, actionable, and encouraging.

You must respond with a single valid JSON object — no markdown code fences, no preamble, no trailing text.

The JSON must conform exactly to this structure:
{
  "feedback_text": "<full feedback message as a professional letter>",
  "rejection_stage": "<the stage at which the candidate was rejected: 'cv_review', 'screening', or 'technical'>"
}

Strict rules you MUST follow:
- Do NOT include any numeric scores, ratings, or percentages in the feedback text.
- Do NOT reference any rubric criteria names, scoring dimensions, or internal evaluation categories.
- Do NOT mention any internal tools, scoring systems, or evaluation frameworks.
- Do NOT include phrases like "you scored", "your score", "rated", "points", or any similar language.
- The feedback MUST acknowledge at least one concrete candidate strength observed during the process.
- The feedback MUST include at least one actionable improvement area framed constructively.
- Use a professional, encouraging, and non-discriminatory tone throughout.
- Keep the feedback between 150 and 350 words.
- Address the candidate as "you" rather than by name."""


def _describe_cv_signals(cv_result: dict[str, Any]) -> str:
    lines: list[str] = []
    if cv_result.get("strengths"):
        lines.append("CV strengths: " + "; ".join(cv_result["strengths"][:3]))
    if cv_result.get("gaps"):
        lines.append("CV gaps: " + "; ".join(cv_result["gaps"][:3]))
    if cv_result.get("overall_impression"):
        lines.append(f"Overall CV impression: {cv_result['overall_impression']}")
    return "\n".join(lines)


def _describe_screening_signals(screening_result: dict[str, Any]) -> str:
    lines: list[str] = []
    if screening_result.get("strengths"):
        lines.append("Screening strengths: " + "; ".join(screening_result["strengths"][:3]))
    if screening_result.get("concerns"):
        lines.append("Screening concerns: " + "; ".join(screening_result["concerns"][:3]))
    if screening_result.get("communication_quality"):
        lines.append(f"Communication: {screening_result['communication_quality']}")
    if screening_result.get("motivation_culture_fit"):
        lines.append(f"Motivation / culture fit: {screening_result['motivation_culture_fit']}")
    return "\n".join(lines)


def _describe_technical_signals(technical_result: dict[str, Any]) -> str:
    lines: list[str] = []
    if technical_result.get("strengths_summary"):
        lines.append("Technical strengths: " + "; ".join(technical_result["strengths_summary"][:3]))
    if technical_result.get("improvement_areas"):
        lines.append(
            "Technical improvement areas: " + "; ".join(technical_result["improvement_areas"][:3])
        )
    return "\n".join(lines)


def build_feedback_gen_prompt(
    evaluation_results: dict[str, Any],
    rejection_stage: str,
) -> tuple[str, str]:
    cv_result: dict[str, Any] | None = evaluation_results.get("cv_analysis")
    screening_result: dict[str, Any] | None = evaluation_results.get("screening_eval")
    technical_result: dict[str, Any] | None = evaluation_results.get("technical_eval")

    signal_sections: list[str] = []

    if cv_result:
        signals = _describe_cv_signals(cv_result)
        if signals:
            signal_sections.append(f"## CV Review Signals\n{signals}")

    if screening_result:
        signals = _describe_screening_signals(screening_result)
        if signals:
            signal_sections.append(f"## Screening Interview Signals\n{signals}")

    if technical_result:
        signals = _describe_technical_signals(technical_result)
        if signals:
            signal_sections.append(f"## Technical Interview Signals\n{signals}")

    signals_block = (
        "\n\n".join(signal_sections)
        if signal_sections
        else "No detailed evaluation signals are available."
    )

    user_prompt = f"""Write a professional rejection feedback letter for a candidate who was not selected after the {rejection_stage} stage of our hiring process.

Use the evaluation signals below as context for crafting personalised, constructive feedback. Do NOT copy or repeat any of these signals verbatim — use them only to inform the tone and specific points you make.

{signals_block}

---

Requirements:
- Rejection stage: {rejection_stage}
- Acknowledge at least one observed strength.
- Provide at least one actionable improvement suggestion.
- Do not include scores, ratings, or internal evaluation details of any kind.
- Keep the tone professional, constructive, and encouraging.

Respond with a single JSON object matching the schema in your instructions. Do not wrap it in markdown code fences."""

    return SYSTEM_PROMPT, user_prompt
