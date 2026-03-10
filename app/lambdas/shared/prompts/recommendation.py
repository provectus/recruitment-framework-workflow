from typing import Any

SYSTEM_PROMPT = """You are a senior recruitment analyst making a final hiring recommendation. Your role is to synthesize evidence from multiple evaluation stages and produce a clear, reasoned recommendation.

You must respond with a single valid JSON object — no markdown code fences, no preamble, no trailing text.

The JSON must conform exactly to this structure:
{
  "recommendation": "hire" | "no_hire" | "needs_discussion",
  "confidence": "high" | "medium" | "low",
  "reasoning": "<narrative referencing specific evidence from prior evaluation steps>",
  "missing_inputs": ["<step_name>"]
}

Field definitions:
- recommendation: your overall hiring recommendation
  - "hire": candidate is a strong fit and should move forward
  - "no_hire": candidate is not a good fit
  - "needs_discussion": evidence is mixed or insufficient to decide without human judgment
- confidence: your confidence level in this recommendation
  - CRITICAL RULE: if ANY evaluation input is marked as NOT AVAILABLE, you MUST set confidence to "low" — never "medium" or "high"
  - "high": all inputs available and evidence is clear and consistent
  - "medium": all inputs available but evidence is mixed or nuanced
  - "low": one or more inputs are missing, OR evidence is contradictory
- reasoning: 3-5 sentence narrative citing specific findings from the available evaluation steps
- missing_inputs: list of step names that were NOT AVAILABLE (e.g. ["cv_analysis", "screening_eval"]); empty list [] if all inputs were present

Guidelines:
- Base your recommendation only on evidence present in the provided evaluation results.
- When inputs are missing, acknowledge the gap explicitly in your reasoning.
- Do not invent information not present in the provided evaluations.
- The missing_inputs field must accurately list every step that shows "NOT AVAILABLE"."""


def _format_cv_analysis(result: dict[str, Any] | None) -> str:
    if result is None:
        return "NOT AVAILABLE - this evaluation step was not completed or failed"

    lines = ["CV Analysis Results:"]

    skills_match = result.get("skills_match", [])
    if skills_match:
        present = [s["skill"] for s in skills_match if s.get("present")]
        missing = [s["skill"] for s in skills_match if not s.get("present")]
        if present:
            lines.append(f"  Skills present: {', '.join(present)}")
        if missing:
            lines.append(f"  Skills absent: {', '.join(missing)}")

    for field in ("experience_relevance", "education", "signals_and_red_flags", "overall_fit"):
        value = result.get(field)
        if value:
            label = field.replace("_", " ").title()
            lines.append(f"  {label}: {value}")

    return "\n".join(lines)


def _format_screening_eval(result: dict[str, Any] | None) -> str:
    if result is None:
        return "NOT AVAILABLE - this evaluation step was not completed or failed"

    lines = ["Screening Interview Results:"]

    key_topics = result.get("key_topics", [])
    if key_topics:
        lines.append(f"  Key topics: {', '.join(key_topics)}")

    strengths = result.get("strengths", [])
    if strengths:
        lines.append(f"  Strengths: {'; '.join(strengths)}")

    concerns = result.get("concerns", [])
    if concerns:
        lines.append(f"  Concerns: {'; '.join(concerns)}")

    for field in ("communication_quality", "motivation_culture_fit"):
        value = result.get(field)
        if value:
            label = field.replace("_", " ").title()
            lines.append(f"  {label}: {value}")

    return "\n".join(lines)


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

    user_prompt = f"""Synthesize the evaluation results below and produce a final hiring recommendation for the position.

## Position: {position_title}

### Requirements
{position_description}

---

## Evaluation Results

### 1. CV Analysis

{cv_section}

### 2. Screening Interview

{screening_section}

### 3. Technical Interview

{technical_section}

---
{confidence_note}
Respond with a single JSON object matching the schema in your instructions. Do not wrap it in markdown code fences."""

    return SYSTEM_PROMPT, user_prompt
