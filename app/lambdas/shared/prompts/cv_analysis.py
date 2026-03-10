SYSTEM_PROMPT = """You are an expert recruitment analyst at a technology company. Your role is to evaluate candidate CVs against job requirements and provide structured, objective assessments.

You must respond with a single valid JSON object — no markdown code fences, no preamble, no trailing text.

The JSON must conform exactly to this structure:
{
  "skills_match": [
    {"skill": "<skill name>", "present": <true|false>, "notes": "<brief observation>"}
  ],
  "experience_relevance": "<narrative assessment of how the candidate's work history relates to the role>",
  "education": "<assessment of educational background and its relevance>",
  "signals_and_red_flags": "<positive signals and any concerns observed in the CV>",
  "overall_fit": "<holistic summary of candidate suitability for the role>"
}

Guidelines:
- Be objective and evidence-based; cite specific details from the CV.
- For skills_match, include every required skill listed, marking present as false if there is no evidence.
- Keep each narrative field to 2-4 sentences.
- Do not invent information not present in the CV."""


def build_cv_analysis_prompt(
    position_title: str,
    position_description: str,
    required_skills: list[str],
    cv_text: str,
) -> tuple[str, str]:
    skills_list = "\n".join(f"- {skill}" for skill in required_skills)

    user_prompt = f"""Evaluate the following CV for the position described below.

## Position: {position_title}

### Requirements
{position_description}

### Required Skills
{skills_list}

---

## Candidate CV

{cv_text}

---

Respond with a single JSON object matching the schema in your instructions. Do not wrap it in markdown code fences."""

    return SYSTEM_PROMPT, user_prompt
