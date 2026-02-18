from typing import Literal

from sqlalchemy import func as sa_func
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.exceptions import ConflictError, NotFoundException, ValidationError
from app.models.position import Position
from app.models.position_rubric import PositionRubric, PositionRubricVersion
from app.models.rubric_template import RubricTemplate
from app.models.user import User


async def create_rubric(
    session: AsyncSession,
    position_id: int,
    source: Literal["template", "custom"],
    template_id: int | None,
    structure_dict: dict | None,
    user_id: int,
) -> dict:
    position = await session.get(Position, position_id)
    if not position or position.is_archived:
        raise NotFoundException(detail="Position not found")

    existing_stmt = select(PositionRubric).where(
        PositionRubric.position_id == position_id
    )
    existing_result = await session.exec(existing_stmt)
    if existing_result.first():
        raise ConflictError(detail="Position already has a rubric assigned")

    source_template_id: int | None = None

    if source == "template":
        if template_id is None:
            raise ValidationError(detail="template_id is required for template source")
        template = await session.get(RubricTemplate, template_id)
        if not template or template.is_archived:
            raise NotFoundException(detail="Template not found")
        structure_dict = dict(template.structure)
        source_template_id = template.id
    elif source == "custom":
        if structure_dict is None:
            raise ValidationError(detail="structure is required for custom source")

    rubric = PositionRubric(
        position_id=position_id,
        source_template_id=source_template_id,
    )
    session.add(rubric)
    await session.flush()

    version = PositionRubricVersion(
        position_rubric_id=rubric.id,
        version_number=1,
        structure=structure_dict,
        created_by_id=user_id,
    )
    session.add(version)
    await session.commit()
    await session.refresh(rubric)
    await session.refresh(version)

    return await _build_rubric_response(session, rubric, version)


async def get_active_rubric(session: AsyncSession, position_id: int) -> dict:
    rubric_stmt = select(PositionRubric).where(
        PositionRubric.position_id == position_id
    )
    rubric_result = await session.exec(rubric_stmt)
    rubric = rubric_result.first()
    if rubric is None:
        raise NotFoundException(detail="No rubric found for this position")

    version_stmt = (
        select(PositionRubricVersion)
        .where(PositionRubricVersion.position_rubric_id == rubric.id)
        .order_by(PositionRubricVersion.version_number.desc())
    )
    version_result = await session.exec(version_stmt)
    version = version_result.first()
    if version is None:
        raise NotFoundException(detail="No rubric version found")

    return await _build_rubric_response(session, rubric, version)


async def _get_rubric_for_position(
    session: AsyncSession, position_id: int, *, lock: bool = False
) -> PositionRubric:
    stmt = select(PositionRubric).where(PositionRubric.position_id == position_id)
    if lock:
        stmt = stmt.with_for_update()
    result = await session.exec(stmt)
    rubric = result.first()
    if rubric is None:
        raise NotFoundException(detail="No rubric found for this position")
    return rubric


async def _get_max_version(session: AsyncSession, rubric_id: int) -> int:
    stmt = select(sa_func.max(PositionRubricVersion.version_number)).where(
        PositionRubricVersion.position_rubric_id == rubric_id
    )
    result = await session.exec(stmt)
    max_version = result.one()
    return max_version if max_version is not None else 0


async def _build_rubric_response(
    session: AsyncSession, rubric: PositionRubric, version: PositionRubricVersion
) -> dict:
    creator = await session.get(User, version.created_by_id)
    creator_name = creator.full_name if creator else str(version.created_by_id)

    template_name: str | None = None
    if rubric.source_template_id is not None:
        template = await session.get(RubricTemplate, rubric.source_template_id)
        template_name = template.name if template else None

    return {
        "id": rubric.id,
        "position_id": rubric.position_id,
        "source_template_name": template_name,
        "version_number": version.version_number,
        "structure": version.structure,
        "created_by": creator_name,
        "created_at": version.created_at,
    }


async def update_rubric(
    session: AsyncSession,
    position_id: int,
    structure_dict: dict,
    user_id: int,
) -> dict:
    rubric = await _get_rubric_for_position(session, position_id, lock=True)
    max_version = await _get_max_version(session, rubric.id)

    new_version = PositionRubricVersion(
        position_rubric_id=rubric.id,
        version_number=max_version + 1,
        structure=structure_dict,
        created_by_id=user_id,
    )
    session.add(new_version)
    await session.commit()
    await session.refresh(new_version)

    return await _build_rubric_response(session, rubric, new_version)


async def delete_rubric(session: AsyncSession, position_id: int) -> None:
    rubric = await _get_rubric_for_position(session, position_id)
    await session.delete(rubric)
    await session.commit()


async def list_versions(session: AsyncSession, position_id: int) -> list[dict]:
    rubric = await _get_rubric_for_position(session, position_id)

    stmt = (
        select(PositionRubricVersion)
        .where(PositionRubricVersion.position_rubric_id == rubric.id)
        .order_by(PositionRubricVersion.version_number.desc())
    )
    result = await session.exec(stmt)
    versions = result.all()

    items = []
    for version in versions:
        creator = await session.get(User, version.created_by_id)
        creator_name = creator.full_name if creator else str(version.created_by_id)
        items.append(
            {
                "version_number": version.version_number,
                "created_by": creator_name,
                "created_at": version.created_at,
            }
        )
    return items


async def get_version(
    session: AsyncSession, position_id: int, version_number: int
) -> dict:
    rubric = await _get_rubric_for_position(session, position_id)

    stmt = select(PositionRubricVersion).where(
        PositionRubricVersion.position_rubric_id == rubric.id,
        PositionRubricVersion.version_number == version_number,
    )
    result = await session.exec(stmt)
    version = result.first()
    if version is None:
        raise NotFoundException(detail="Rubric version not found")

    return await _build_rubric_response(session, rubric, version)


async def revert_to_version(
    session: AsyncSession, position_id: int, version_number: int, user_id: int
) -> dict:
    rubric = await _get_rubric_for_position(session, position_id, lock=True)

    stmt = select(PositionRubricVersion).where(
        PositionRubricVersion.position_rubric_id == rubric.id,
        PositionRubricVersion.version_number == version_number,
    )
    result = await session.exec(stmt)
    target_version = result.first()
    if target_version is None:
        raise NotFoundException(detail="Rubric version not found")

    max_version = await _get_max_version(session, rubric.id)

    new_version = PositionRubricVersion(
        position_rubric_id=rubric.id,
        version_number=max_version + 1,
        structure=dict(target_version.structure),
        created_by_id=user_id,
    )
    session.add(new_version)
    await session.commit()
    await session.refresh(new_version)

    return await _build_rubric_response(session, rubric, new_version)


async def save_as_template(
    session: AsyncSession,
    position_id: int,
    name: str,
    description: str | None,
) -> dict:
    rubric = await _get_rubric_for_position(session, position_id)
    max_version = await _get_max_version(session, rubric.id)

    version_stmt = select(PositionRubricVersion).where(
        PositionRubricVersion.position_rubric_id == rubric.id,
        PositionRubricVersion.version_number == max_version,
    )
    version_result = await session.exec(version_stmt)
    active_version = version_result.first()
    if active_version is None:
        raise NotFoundException(detail="No rubric version found")

    template = RubricTemplate(
        name=name,
        description=description,
        structure=dict(active_version.structure),
    )
    session.add(template)
    await session.commit()
    await session.refresh(template)

    return {
        "id": template.id,
        "name": template.name,
        "description": template.description,
        "structure": template.structure,
        "is_archived": template.is_archived,
        "created_at": template.created_at,
        "updated_at": template.updated_at,
    }
