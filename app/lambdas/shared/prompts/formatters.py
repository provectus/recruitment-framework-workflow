from typing import Any

CV_ANALYSIS_ALL_FIELDS = (
    "experience_relevance",
    "education",
    "signals_and_red_flags",
    "overall_fit",
)


def format_cv_analysis_result(
    result: dict[str, Any],
    fields: tuple[str, ...] = CV_ANALYSIS_ALL_FIELDS,
) -> str:
    lines: list[str] = ["CV Analysis Results:"]

    skills_match = result.get("skills_match", [])
    if skills_match:
        present = [s["skill"] for s in skills_match if s.get("present")]
        missing = [s["skill"] for s in skills_match if not s.get("present")]
        if present:
            lines.append(f"  Skills present: {', '.join(present)}")
        if missing:
            lines.append(f"  Skills absent: {', '.join(missing)}")

    for field in fields:
        value = result.get(field)
        if value:
            label = field.replace("_", " ").title()
            lines.append(f"  {label}: {value}")

    return "\n".join(lines)


def format_screening_result(
    result: dict[str, Any],
    include_key_topics: bool = True,
) -> str:
    lines: list[str] = ["Screening Interview Results:"]

    if include_key_topics:
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

    requirements_alignment = result.get("requirements_alignment", [])
    if requirements_alignment:
        lines.append("  Requirements alignment:")
        for entry in requirements_alignment:
            req = entry.get("requirement", "Unknown")
            status = entry.get("status", "unknown")
            evidence = entry.get("evidence", "")
            lines.append(f"    - {req}: {status} — {evidence}")

    return "\n".join(lines)
