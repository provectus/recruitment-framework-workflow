from typing import Any

SYSTEM_PROMPT = """You evaluate candidate CVs against job requirements. You produce structured, objective assessments.

Rules:
- Be objective and evidence-based; cite specific details from the CV.
- For skills_match, include every required skill listed, marking present as false if there is no evidence.
- Keep each narrative field to 2-4 sentences.
- Do not invent information not present in the CV."""

TOOL_NAME = "cv_analysis"

TOOL_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "thinking": {
            "type": "string",
            "description": "Your internal reasoning about the candidate's fit before producing the structured assessment. Consider skills gaps, experience alignment, and overall suitability.",
        },
        "skills_match": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "skill": {"type": "string"},
                    "present": {"type": "boolean"},
                    "notes": {"type": "string", "description": "Brief observation from the CV"},
                },
                "required": ["skill", "present", "notes"],
            },
            "description": "One entry per required skill listed in the position requirements.",
        },
        "experience_relevance": {
            "type": "string",
            "description": "2-4 sentence assessment of how the candidate's work history relates to the role.",
        },
        "education": {
            "type": "string",
            "description": "2-4 sentence assessment of educational background and its relevance.",
        },
        "signals_and_red_flags": {
            "type": "string",
            "description": "2-4 sentence summary of positive signals and any concerns observed in the CV.",
        },
        "overall_fit": {
            "type": "string",
            "description": "2-4 sentence holistic summary of candidate suitability for the role.",
        },
    },
    "required": [
        "thinking",
        "skills_match",
        "experience_relevance",
        "education",
        "signals_and_red_flags",
        "overall_fit",
    ],
}


def build_cv_analysis_prompt(
    position_title: str,
    position_description: str,
    required_skills: list[str],
    cv_text: str,
    evaluation_instructions: str = "",
) -> tuple[str, str]:
    skills_list = "\n".join(f"- {skill}" for skill in required_skills)

    instructions_section = ""
    if evaluation_instructions:
        instructions_section = f"""

## Evaluation Instructions

{evaluation_instructions}

---
"""

    user_prompt = f"""Evaluate the following CV for the position described below.

## Position: {position_title}

### Requirements
{position_description}

### Required Skills
{skills_list}

---
{instructions_section}
## Candidate CV

{cv_text}"""

    return SYSTEM_PROMPT, user_prompt
