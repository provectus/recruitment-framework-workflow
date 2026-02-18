"""seed_default_rubric_templates

Revision ID: a1b2c3d4e5f6
Revises: 6ab559edd7eb
Create Date: 2026-02-18 00:00:00.000000

"""

import json
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "a1b2c3d4e5f6"
down_revision: str | Sequence[str] | None = "6ab559edd7eb"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _category(
    name: str,
    description: str,
    weight: int,
    sort_order: int,
    criteria: list[dict],
) -> dict:
    return {
        "name": name,
        "description": description,
        "weight": weight,
        "sort_order": sort_order,
        "criteria": criteria,
    }


def _criterion(
    name: str,
    description: str,
    weight: int,
    sort_order: int,
) -> dict:
    return {
        "name": name,
        "description": description,
        "weight": weight,
        "sort_order": sort_order,
    }


_SOFTWARE_ENGINEER_STRUCTURE = {
    "categories": [
        _category(
            name="Technical Skills",
            description="Core technical competencies required for the role",
            weight=40,
            sort_order=0,
            criteria=[
                _criterion(
                    "System Design",
                    "Ability to design scalable and maintainable systems",
                    30,
                    0,
                ),
                _criterion(
                    "Coding Proficiency",
                    "Code quality, efficiency, and adherence to best practices",
                    40,
                    1,
                ),
                _criterion(
                    "Problem Solving",
                    "Analytical and algorithmic thinking under constraints",
                    30,
                    2,
                ),
            ],
        ),
        _category(
            name="Communication",
            description=(
                "Ability to convey technical ideas clearly to various audiences"
            ),
            weight=25,
            sort_order=1,
            criteria=[
                _criterion(
                    "Verbal Clarity",
                    "Articulates ideas and reasoning clearly in spoken form",
                    50,
                    0,
                ),
                _criterion(
                    "Written Communication",
                    "Produces clear documentation, comments, and written updates",
                    50,
                    1,
                ),
            ],
        ),
        _category(
            name="Culture & Collaboration",
            description="Ability to work effectively within a team environment",
            weight=20,
            sort_order=2,
            criteria=[
                _criterion(
                    "Team Collaboration",
                    "Contributes positively to team dynamics and shared goals",
                    50,
                    0,
                ),
                _criterion(
                    "Adaptability",
                    "Adjusts effectively to changing priorities and environments",
                    50,
                    1,
                ),
            ],
        ),
        _category(
            name="Leadership & Growth",
            description=(
                "Demonstrates ownership, initiative, and continuous improvement"
            ),
            weight=15,
            sort_order=3,
            criteria=[
                _criterion(
                    "Initiative",
                    "Proactively identifies and addresses problems or opportunities",
                    50,
                    0,
                ),
                _criterion(
                    "Learning Mindset",
                    "Actively seeks feedback and invests in skill development",
                    50,
                    1,
                ),
            ],
        ),
    ]
}

_PRODUCT_MANAGER_STRUCTURE = {
    "categories": [
        _category(
            name="Product Strategy",
            description=(
                "Ability to define and drive a coherent product vision and roadmap"
            ),
            weight=35,
            sort_order=0,
            criteria=[
                _criterion(
                    "Market Analysis",
                    "Understands market dynamics, competitors, and customer needs",
                    40,
                    0,
                ),
                _criterion(
                    "Roadmap Planning",
                    "Builds realistic, outcome-oriented product roadmaps",
                    35,
                    1,
                ),
                _criterion(
                    "Prioritization",
                    "Makes defensible trade-offs to maximize value delivery",
                    25,
                    2,
                ),
            ],
        ),
        _category(
            name="Stakeholder Management",
            description="Ability to align and influence diverse stakeholders",
            weight=25,
            sort_order=1,
            criteria=[
                _criterion(
                    "Cross-functional Communication",
                    "Collaborates with engineering, design, and business teams",
                    50,
                    0,
                ),
                _criterion(
                    "Executive Presentation",
                    "Presents strategy and progress clearly to leadership",
                    50,
                    1,
                ),
            ],
        ),
        _category(
            name="Analytical Skills",
            description="Ability to use data to inform decisions and measure outcomes",
            weight=25,
            sort_order=2,
            criteria=[
                _criterion(
                    "Data-Driven Decision Making",
                    "Grounds product decisions in qualitative and quantitative data",
                    60,
                    0,
                ),
                _criterion(
                    "Metrics Definition",
                    "Defines meaningful KPIs and success criteria for features",
                    40,
                    1,
                ),
            ],
        ),
        _category(
            name="Leadership",
            description="Ability to inspire and guide teams without direct authority",
            weight=15,
            sort_order=3,
            criteria=[
                _criterion(
                    "Team Influence",
                    "Motivates and aligns team members toward shared objectives",
                    50,
                    0,
                ),
                _criterion(
                    "Vision Setting",
                    "Articulates a compelling long-term product direction",
                    50,
                    1,
                ),
            ],
        ),
    ]
}

_DESIGNER_STRUCTURE = {
    "categories": [
        _category(
            name="Design Skills",
            description=(
                "Core craft competencies across visual, UX, and prototyping domains"
            ),
            weight=40,
            sort_order=0,
            criteria=[
                _criterion(
                    "Visual Design",
                    "Applies strong typography, colour, and layout principles",
                    35,
                    0,
                ),
                _criterion(
                    "UX Research",
                    "Plans and executes user research to validate design decisions",
                    35,
                    1,
                ),
                _criterion(
                    "Prototyping",
                    "Creates interactive prototypes to communicate and test ideas",
                    30,
                    2,
                ),
            ],
        ),
        _category(
            name="Problem Solving",
            description=(
                "Ability to frame and resolve design challenges systematically"
            ),
            weight=25,
            sort_order=1,
            criteria=[
                _criterion(
                    "Design Thinking",
                    "Applies structured frameworks to move from problem to solution",
                    50,
                    0,
                ),
                _criterion(
                    "User Empathy",
                    "Deeply understands and advocates for user needs and pain points",
                    50,
                    1,
                ),
            ],
        ),
        _category(
            name="Collaboration",
            description=(
                "Ability to work effectively with engineers and other stakeholders"
            ),
            weight=20,
            sort_order=2,
            criteria=[
                _criterion(
                    "Developer Handoff",
                    "Produces complete, annotated specs that unblock engineering",
                    50,
                    0,
                ),
                _criterion(
                    "Feedback Integration",
                    "Receives critique constructively and iterates on designs",
                    50,
                    1,
                ),
            ],
        ),
        _category(
            name="Communication",
            description="Ability to present and document design work effectively",
            weight=15,
            sort_order=3,
            criteria=[
                _criterion(
                    "Design Presentation",
                    "Articulates design rationale and trade-offs persuasively",
                    60,
                    0,
                ),
                _criterion(
                    "Documentation",
                    "Maintains clear design system docs and decision records",
                    40,
                    1,
                ),
            ],
        ),
    ]
}

_DATA_SCIENTIST_STRUCTURE = {
    "categories": [
        _category(
            name="Technical Skills",
            description="Core quantitative and engineering competencies",
            weight=40,
            sort_order=0,
            criteria=[
                _criterion(
                    "Statistical Modeling",
                    "Selects and applies appropriate statistical methods to problems",
                    35,
                    0,
                ),
                _criterion(
                    "Machine Learning",
                    "Builds, evaluates, and deploys ML models at appropriate scale",
                    35,
                    1,
                ),
                _criterion(
                    "Data Engineering",
                    "Constructs reliable data pipelines and manages data quality",
                    30,
                    2,
                ),
            ],
        ),
        _category(
            name="Business Acumen",
            description="Ability to connect analytical work to business value",
            weight=25,
            sort_order=1,
            criteria=[
                _criterion(
                    "Problem Framing",
                    "Translates ambiguous business questions into analytical problems",
                    50,
                    0,
                ),
                _criterion(
                    "Stakeholder Communication",
                    "Explains complex findings to non-technical audiences clearly",
                    50,
                    1,
                ),
            ],
        ),
        _category(
            name="Research & Analysis",
            description=(
                "Rigour and creativity in designing and interpreting analyses"
            ),
            weight=20,
            sort_order=2,
            criteria=[
                _criterion(
                    "Experiment Design",
                    "Designs statistically sound A/B tests and observational studies",
                    50,
                    0,
                ),
                _criterion(
                    "Data Visualization",
                    "Creates insightful charts and dashboards that drive decisions",
                    50,
                    1,
                ),
            ],
        ),
        _category(
            name="Collaboration",
            description=(
                "Ability to operate effectively within cross-functional teams"
            ),
            weight=15,
            sort_order=3,
            criteria=[
                _criterion(
                    "Cross-functional Work",
                    "Partners with product, engineering, and business teams",
                    50,
                    0,
                ),
                _criterion(
                    "Knowledge Sharing",
                    "Disseminates analytical methods and findings across the org",
                    50,
                    1,
                ),
            ],
        ),
    ]
}

_TEMPLATES = [
    {
        "name": "Software Engineer",
        "description": ("Standard evaluation rubric for software engineering roles"),
        "structure": json.dumps(_SOFTWARE_ENGINEER_STRUCTURE),
    },
    {
        "name": "Product Manager",
        "description": ("Standard evaluation rubric for product management roles"),
        "structure": json.dumps(_PRODUCT_MANAGER_STRUCTURE),
    },
    {
        "name": "Designer",
        "description": "Standard evaluation rubric for UX/product design roles",
        "structure": json.dumps(_DESIGNER_STRUCTURE),
    },
    {
        "name": "Data Scientist",
        "description": "Standard evaluation rubric for data science roles",
        "structure": json.dumps(_DATA_SCIENTIST_STRUCTURE),
    },
]

_SEEDED_NAMES = [t["name"] for t in _TEMPLATES]

_INSERT_SQL = sa.text(
    "INSERT INTO rubric_templates"
    " (name, description, structure, is_archived, created_at, updated_at)"
    " VALUES"
    " (:name, :description, :structure, false,"
    " CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)"
)

_DELETE_SQL = sa.text("DELETE FROM rubric_templates WHERE name = :name")


def upgrade() -> None:
    """Seed default rubric templates if the table is empty."""
    conn = op.get_bind()
    result = conn.execute(sa.text("SELECT COUNT(*) FROM rubric_templates"))
    count = result.scalar()
    if count and count > 0:
        return
    for template in _TEMPLATES:
        conn.execute(_INSERT_SQL, template)


def downgrade() -> None:
    """Remove seeded default rubric templates."""
    conn = op.get_bind()
    for name in _SEEDED_NAMES:
        conn.execute(_DELETE_SQL, {"name": name})
