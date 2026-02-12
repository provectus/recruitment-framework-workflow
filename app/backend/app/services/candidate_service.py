from sqlalchemy import func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models.candidate import Candidate
from app.models.candidate_position import CandidatePosition
from app.models.enums import PipelineStage
from app.models.position import Position

VALID_TRANSITIONS: dict[str, list[str]] = {
    "new": ["screening", "rejected"],
    "screening": ["technical", "rejected"],
    "technical": ["offer", "rejected"],
    "offer": ["hired", "rejected"],
    "hired": [],
    "rejected": [],
}


def get_valid_next_stages(current_stage: str) -> list[str]:
    """Return list of valid next stages from the current stage."""
    return VALID_TRANSITIONS.get(current_stage, [])


def validate_stage_transition(current_stage: str, new_stage: str) -> bool:
    """Check if a stage transition is valid."""
    return new_stage in get_valid_next_stages(current_stage)


async def list_candidates(
    session: AsyncSession,
    offset: int = 0,
    limit: int = 20,
    search: str | None = None,
    stage: str | None = None,
    position_id: int | None = None,
    sort_by: str | None = None,
    sort_order: str | None = None,
) -> tuple[list[dict], int]:
    allowed_sort_columns = {"full_name", "email", "updated_at"}
    sort_column = sort_by if sort_by in allowed_sort_columns else "updated_at"
    order_direction = sort_order if sort_order in {"asc", "desc"} else "desc"

    count_stmt = select(func.count(Candidate.id.distinct())).select_from(Candidate)
    stmt = select(Candidate).distinct()

    needs_join = stage is not None or position_id is not None
    if needs_join:
        count_stmt = count_stmt.join(
            CandidatePosition, Candidate.id == CandidatePosition.candidate_id
        )
        stmt = stmt.join(
            CandidatePosition, Candidate.id == CandidatePosition.candidate_id
        )

    filters = [Candidate.is_archived.is_(False)]

    if search:
        filters.append(
            or_(
                Candidate.full_name.ilike(f"%{search}%"),
                Candidate.email.ilike(f"%{search}%"),
            )
        )

    if stage:
        filters.append(CandidatePosition.stage == stage)

    if position_id:
        filters.append(CandidatePosition.position_id == position_id)

    count_stmt = count_stmt.where(*filters)
    count_result = await session.exec(count_stmt)
    total_count = count_result.one()[0]

    sort_attr = getattr(Candidate, sort_column)
    order_clause = (
        sort_attr.asc() if order_direction == "asc" else sort_attr.desc()
    )

    stmt = (
        stmt.where(*filters).order_by(order_clause).offset(offset).limit(limit)
    )
    result = await session.exec(stmt)
    candidates = list(result.scalars().all())

    if not candidates:
        return [], total_count

    candidate_ids = [c.id for c in candidates]

    positions_stmt = (
        select(CandidatePosition, Position)
        .join(Position, CandidatePosition.position_id == Position.id)
        .where(CandidatePosition.candidate_id.in_(candidate_ids))
    )
    positions_result = await session.exec(positions_stmt)
    positions_rows = positions_result.all()

    positions_by_candidate: dict[int, list[dict]] = {}
    for row in positions_rows:
        candidate_id = row[0].candidate_id
        if candidate_id not in positions_by_candidate:
            positions_by_candidate[candidate_id] = []
        positions_by_candidate[candidate_id].append(
            {
                "position_id": row[1].id,
                "position_title": row[1].title,
                "stage": row[0].stage,
            }
        )

    items = [
        {
            "id": candidate.id,
            "full_name": candidate.full_name,
            "email": candidate.email,
            "positions": positions_by_candidate.get(candidate.id, []),
            "updated_at": candidate.updated_at.isoformat(),
        }
        for candidate in candidates
    ]

    return items, total_count


async def create_candidate(
    session: AsyncSession,
    full_name: str,
    email: str,
) -> Candidate:
    stmt = select(Candidate).where(func.lower(Candidate.email) == email.lower())
    result = await session.exec(stmt)
    existing = result.one_or_none()

    if existing:
        raise ValueError("A candidate with this email already exists.")

    candidate = Candidate(
        full_name=full_name,
        email=email,
    )
    session.add(candidate)
    await session.commit()
    await session.refresh(candidate)
    return candidate


async def get_candidate(session: AsyncSession, candidate_id: int) -> Candidate | None:
    candidate = await session.get(Candidate, candidate_id)
    if candidate is None or candidate.is_archived:
        return None
    return candidate


async def update_candidate(
    session: AsyncSession,
    candidate_id: int,
    full_name: str | None = None,
    email: str | None = None,
) -> Candidate:
    candidate = await session.get(Candidate, candidate_id)
    if candidate is None or candidate.is_archived:
        raise ValueError("Candidate not found")

    if email is not None:
        stmt = select(Candidate).where(
            func.lower(Candidate.email) == email.lower(),
            Candidate.id != candidate_id,
        )
        result = await session.exec(stmt)
        existing = result.one_or_none()
        if existing:
            raise ValueError("A candidate with this email already exists.")

    if full_name is not None:
        candidate.full_name = full_name
    if email is not None:
        candidate.email = email

    session.add(candidate)
    await session.commit()
    await session.refresh(candidate)
    return candidate


async def add_to_position(
    session: AsyncSession,
    candidate_id: int,
    position_id: int,
) -> CandidatePosition:
    candidate = await session.get(Candidate, candidate_id)
    if candidate is None or candidate.is_archived:
        raise ValueError("Candidate not found")

    position = await session.get(Position, position_id)
    if position is None or position.is_archived:
        raise ValueError("Position not found")

    stmt = select(CandidatePosition).where(
        CandidatePosition.candidate_id == candidate_id,
        CandidatePosition.position_id == position_id,
    )
    result = await session.exec(stmt)
    existing = result.one_or_none()

    if existing:
        raise ValueError("Candidate is already associated with this position.")

    candidate_position = CandidatePosition(
        candidate_id=candidate_id,
        position_id=position_id,
        stage=PipelineStage.new.value,
    )
    session.add(candidate_position)

    try:
        await session.commit()
        await session.refresh(candidate_position)
    except IntegrityError as e:
        await session.rollback()
        raise ValueError("Candidate is already associated with this position.") from e

    return candidate_position


async def remove_from_position(
    session: AsyncSession,
    candidate_id: int,
    position_id: int,
) -> None:
    stmt = select(CandidatePosition).where(
        CandidatePosition.candidate_id == candidate_id,
        CandidatePosition.position_id == position_id,
    )
    result = await session.exec(stmt)
    candidate_position = result.scalars().first()

    if candidate_position is None:
        raise ValueError("Association not found")

    await session.delete(candidate_position)
    await session.commit()


async def update_stage(
    session: AsyncSession,
    candidate_id: int,
    position_id: int,
    new_stage: str,
) -> CandidatePosition:
    """Update the pipeline stage for a candidate-position link.
    Validate the new_stage is a valid PipelineStage value.
    Validate the transition is allowed (forward-only, reject-from-any,
    no-from-terminal).
    Raise ValueError("Association not found") if link doesn't exist.
    Raise ValueError("Invalid stage") if not a valid PipelineStage.
    Raise ValueError("Invalid stage transition from X to Y")
    if transition not allowed.
    """
    valid_stages = {stage.value for stage in PipelineStage}
    if new_stage not in valid_stages:
        raise ValueError("Invalid stage")

    stmt = select(CandidatePosition).where(
        CandidatePosition.candidate_id == candidate_id,
        CandidatePosition.position_id == position_id,
    )
    result = await session.exec(stmt)
    candidate_position = result.scalars().first()

    if candidate_position is None:
        raise ValueError("Association not found")

    if not validate_stage_transition(candidate_position.stage, new_stage):
        raise ValueError(
            f"Invalid stage transition from {candidate_position.stage} to {new_stage}"
        )

    candidate_position.stage = new_stage
    session.add(candidate_position)
    await session.commit()
    await session.refresh(candidate_position)
    return candidate_position


async def archive_candidate(session: AsyncSession, candidate_id: int) -> Candidate:
    candidate = await session.get(Candidate, candidate_id)
    if candidate is None or candidate.is_archived:
        raise ValueError("Candidate not found")
    candidate.is_archived = True
    session.add(candidate)
    await session.commit()
    await session.refresh(candidate)
    return candidate
