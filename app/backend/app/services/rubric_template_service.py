from sqlalchemy import func as sa_func
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.exceptions import NotFoundException
from app.models.position_rubric import PositionRubric
from app.models.rubric_template import RubricTemplate


async def list_templates(session: AsyncSession) -> list[RubricTemplate]:
    statement = (
        select(RubricTemplate)
        .where(RubricTemplate.is_archived.is_(False))
        .order_by(RubricTemplate.name)
    )
    result = await session.exec(statement)
    return list(result.all())


async def count_positions_by_templates(
    session: AsyncSession, template_ids: list[int]
) -> dict[int, int]:
    if not template_ids:
        return {}
    statement = (
        select(PositionRubric.source_template_id, sa_func.count())
        .where(PositionRubric.source_template_id.in_(template_ids))
        .group_by(PositionRubric.source_template_id)
    )
    result = await session.exec(statement)
    return dict(result.all())


async def create_template(
    session: AsyncSession,
    name: str,
    description: str | None,
    structure: dict,
) -> RubricTemplate:
    template = RubricTemplate(name=name, description=description, structure=structure)
    session.add(template)
    await session.commit()
    await session.refresh(template)
    return template


async def get_template(session: AsyncSession, template_id: int) -> RubricTemplate:
    template = await session.get(RubricTemplate, template_id)
    if not template or template.is_archived:
        raise NotFoundException(detail="Template not found")
    return template


async def update_template(
    session: AsyncSession,
    template_id: int,
    name: str | None = None,
    description: str | None = None,
    structure: dict | None = None,
) -> RubricTemplate:
    template = await get_template(session, template_id)
    if name is not None:
        template.name = name
    if description is not None:
        template.description = description
    if structure is not None:
        template.structure = structure
    session.add(template)
    await session.commit()
    await session.refresh(template)
    return template


async def duplicate_template(session: AsyncSession, template_id: int) -> RubricTemplate:
    original = await get_template(session, template_id)
    copy = RubricTemplate(
        name=f"{original.name} (Copy)",
        description=original.description,
        structure=original.structure,
    )
    session.add(copy)
    await session.commit()
    await session.refresh(copy)
    return copy


async def archive_template(
    session: AsyncSession, template_id: int
) -> tuple[RubricTemplate, int]:
    template = await get_template(session, template_id)
    template.is_archived = True
    session.add(template)
    await session.commit()
    await session.refresh(template)

    count_stmt = select(sa_func.count()).where(
        PositionRubric.source_template_id == template_id
    )
    count_result = await session.exec(count_stmt)
    position_count = count_result.one()

    return template, position_count
