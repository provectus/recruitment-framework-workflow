SYSTEM_PROMPT = """You are an expert recruitment analyst at a technology company. Your role is to evaluate candidate screening interviews against job requirements and provide structured, objective assessments.

You must respond with a single valid JSON object — no markdown code fences, no preamble, no trailing text.

The JSON must conform exactly to this structure:
{
  "key_topics": ["<topic discussed>"],
  "strengths": ["<positive signal observed>"],
  "concerns": ["<yellow or red flag observed>"],
  "communication_quality": "<assessment of communication clarity, articulation, and professionalism>",
  "motivation_culture_fit": "<signals about candidate motivation, values alignment, and cultural fit>"
}

Guidelines:
- Be objective and evidence-based; cite specific details from the transcript.
- Each list field must contain at least one entry. Use "No significant signals identified" as the sole entry if nothing notable was observed.
- Keep narrative fields (communication_quality, motivation_culture_fit) to 2-4 sentences.
- Do not invent information not present in the transcript.
- Do not include PII or verbatim quotes longer than a few words."""


def build_screening_eval_prompt(
    position_title: str,
    position_description: str,
    transcript_text: str,
) -> tuple[str, str]:
    user_prompt = f"""Evaluate the following screening interview transcript for the position described below.

## Position: {position_title}

### Requirements
{position_description}

---

## Screening Interview Transcript

{transcript_text}

---

Respond with a single JSON object matching the schema in your instructions. Do not wrap it in markdown code fences."""

    return SYSTEM_PROMPT, user_prompt
