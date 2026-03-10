from typing import Any

SYSTEM_PROMPT = """You are an expert technical interviewer evaluating a candidate's performance in a structured interview. Your role is to score each rubric criterion based solely on evidence from the interview transcript.

You must respond with a single valid JSON object — no markdown code fences, no preamble, no trailing text.

The JSON must conform exactly to this structure:
{
  "criteria_scores": [
    {
      "criterion_name": "<name>",
      "category_name": "<category>",
      "score": <integer 1-5>,
      "max_score": 5,
      "weight": <decimal>,
      "evidence": "<direct quote or paraphrase from the transcript>",
      "reasoning": "<why this score was assigned>"
    }
  ],
  "weighted_total": <decimal>,
  "strengths_summary": ["<strength 1>", "<strength 2>"],
  "improvement_areas": ["<area 1>", "<area 2>"]
}

Scoring scale:
1 — No evidence of competency
2 — Minimal / insufficient evidence
3 — Adequate, meets baseline expectations
4 — Strong, exceeds expectations
5 — Exceptional, expert-level demonstration

Guidelines:
- Score every criterion listed, even if the transcript contains no relevant discussion (score 1).
- The evidence field must cite specific moments from the transcript.
- Keep reasoning to 2-3 sentences.
- Calculate weighted_total as: sum(score * weight) / sum(weight). We will verify this server-side."""


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


def build_technical_eval_prompt(
    position_title: str,
    position_description: str,
    rubric_structure: dict[str, Any],
    transcript_text: str,
) -> tuple[str, str]:
    formatted_criteria = _format_rubric_criteria(rubric_structure)

    user_prompt = f"""Score the candidate interview transcript for the position described below using the rubric criteria provided.

## Position: {position_title}

### Description
{position_description}

---

## Evaluation Rubric

{formatted_criteria}

---

## Interview Transcript

{transcript_text}

---

Score every criterion from the rubric. For each, provide a score (1-5), the weight as listed, a direct evidence quote from the transcript, and your reasoning. Respond with a single JSON object matching the schema in your instructions. Do not wrap it in markdown code fences."""

    return SYSTEM_PROMPT, user_prompt
