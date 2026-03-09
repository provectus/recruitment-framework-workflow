from sqlmodel.ext.asyncio.session import AsyncSession

from app.models.position import Position
from app.models.rubric_template import RubricTemplate
from app.models.team import Team
from app.models.user import User

VALID_RUBRIC_STRUCTURE = {
    "categories": [
        {
            "name": "Technical",
            "description": None,
            "weight": 60,
            "sort_order": 0,
            "criteria": [
                {
                    "name": "Coding",
                    "description": None,
                    "weight": 50,
                    "sort_order": 0,
                },
                {
                    "name": "Design",
                    "description": None,
                    "weight": 50,
                    "sort_order": 1,
                },
            ],
        },
        {
            "name": "Communication",
            "description": None,
            "weight": 40,
            "sort_order": 1,
            "criteria": [
                {
                    "name": "Clarity",
                    "description": None,
                    "weight": 100,
                    "sort_order": 0,
                },
            ],
        },
    ]
}


async def create_test_position(session: AsyncSession) -> Position:
    user = User(
        email="mgr@test.com",
        google_id="mgr123",
        full_name="Manager",
    )
    session.add(user)
    await session.flush()

    team = Team(name="Engineering")
    session.add(team)
    await session.flush()

    position = Position(
        title="Senior Dev",
        team_id=team.id,
        hiring_manager_id=user.id,
    )
    session.add(position)
    await session.commit()
    await session.refresh(position)
    return position


async def create_test_template(
    session: AsyncSession,
) -> RubricTemplate:
    template = RubricTemplate(
        name="Test Template",
        description="A test template",
        structure=VALID_RUBRIC_STRUCTURE,
    )
    session.add(template)
    await session.commit()
    await session.refresh(template)
    return template
