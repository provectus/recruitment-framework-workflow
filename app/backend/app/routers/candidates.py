from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.database import get_session
from app.dependencies.auth import get_current_user
from app.models.candidate_position import CandidatePosition
from app.models.position import Position
from app.models.user import User
from app.schemas.candidates import (
    CandidateCreate,
    CandidateDetailResponse,
    CandidateListItem,
    CandidatePositionCreate,
    CandidatePositionResponse,
    CandidateResponse,
    CandidateUpdate,
    PaginatedCandidates,
    PositionStageItem,
    StageUpdate,
)
from app.services import candidate_service

router = APIRouter(prefix="/api/candidates", tags=["candidates"])


@router.get("", response_model=PaginatedCandidates)
async def list_candidates(
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    search: str | None = Query(default=None),
    stage: str | None = Query(default=None),
    position_id: int | None = Query(default=None),
    sort_by: str | None = Query(default=None),
    sort_order: str | None = Query(default=None),
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> PaginatedCandidates:
    items, total = await candidate_service.list_candidates(
        session, offset, limit, search, stage, position_id, sort_by, sort_order
    )
    return PaginatedCandidates(
        items=[
            CandidateListItem(
                id=item["id"],
                full_name=item["full_name"],
                email=item["email"],
                positions=[PositionStageItem(**pos) for pos in item["positions"]],
                updated_at=item["updated_at"],
            )
            for item in items
        ],
        total=total,
        offset=offset,
        limit=limit,
    )


@router.post("", response_model=CandidateResponse, status_code=status.HTTP_201_CREATED)
async def create_candidate(
    body: CandidateCreate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> CandidateResponse:
    try:
        candidate = await candidate_service.create_candidate(
            session,
            body.full_name,
            body.email,
        )
        return CandidateResponse(
            id=candidate.id,
            full_name=candidate.full_name,
            email=candidate.email,
            is_archived=candidate.is_archived,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e),
        ) from e


@router.get("/{candidate_id}", response_model=CandidateDetailResponse)
async def get_candidate(
    candidate_id: int,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> CandidateDetailResponse:
    candidate = await candidate_service.get_candidate(session, candidate_id)
    if candidate is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Candidate not found",
        )

    positions_stmt = (
        select(CandidatePosition, Position)
        .join(Position, CandidatePosition.position_id == Position.id)
        .where(CandidatePosition.candidate_id == candidate_id)
    )
    positions_result = await session.exec(positions_stmt)
    positions_rows = positions_result.all()

    positions = [
        PositionStageItem(
            position_id=row.Position.id,
            position_title=row.Position.title,
            stage=row.CandidatePosition.stage,
        )
        for row in positions_rows
    ]

    return CandidateDetailResponse(
        id=candidate.id,
        full_name=candidate.full_name,
        email=candidate.email,
        is_archived=candidate.is_archived,
        positions=positions,
        created_at=candidate.created_at.isoformat(),
        updated_at=candidate.updated_at.isoformat(),
    )


@router.patch("/{candidate_id}", response_model=CandidateResponse)
async def update_candidate(
    candidate_id: int,
    body: CandidateUpdate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> CandidateResponse:
    try:
        candidate = await candidate_service.update_candidate(
            session,
            candidate_id,
            body.full_name,
            body.email,
        )
        return CandidateResponse(
            id=candidate.id,
            full_name=candidate.full_name,
            email=candidate.email,
            is_archived=candidate.is_archived,
        )
    except ValueError as e:
        error_msg = str(e)
        if "not found" in error_msg.lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=error_msg,
            ) from e
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=error_msg,
        ) from e


@router.post(
    "/{candidate_id}/positions",
    response_model=CandidatePositionResponse,
    status_code=status.HTTP_201_CREATED,
)
async def add_to_position(
    candidate_id: int,
    body: CandidatePositionCreate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> CandidatePositionResponse:
    try:
        candidate_position = await candidate_service.add_to_position(
            session,
            candidate_id,
            body.position_id,
        )
        return CandidatePositionResponse(
            id=candidate_position.id,
            candidate_id=candidate_position.candidate_id,
            position_id=candidate_position.position_id,
            stage=candidate_position.stage,
            created_at=candidate_position.created_at.isoformat(),
            updated_at=candidate_position.updated_at.isoformat(),
        )
    except ValueError as e:
        error_msg = str(e)
        if "not found" in error_msg.lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=error_msg,
            ) from e
        if "already associated" in error_msg.lower():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=error_msg,
            ) from e
        raise


@router.delete(
    "/{candidate_id}/positions/{position_id}", status_code=status.HTTP_204_NO_CONTENT
)
async def remove_from_position(
    candidate_id: int,
    position_id: int,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> None:
    try:
        await candidate_service.remove_from_position(
            session,
            candidate_id,
            position_id,
        )
    except ValueError as e:
        error_msg = str(e)
        if "not found" in error_msg.lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=error_msg,
            ) from e
        raise


@router.patch(
    "/{candidate_id}/positions/{position_id}", response_model=CandidatePositionResponse
)
async def update_stage(
    candidate_id: int,
    position_id: int,
    body: StageUpdate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> CandidatePositionResponse:
    """Update pipeline stage. Return 404 if not found, 422 if invalid transition."""
    try:
        candidate_position = await candidate_service.update_stage(
            session,
            candidate_id,
            position_id,
            body.stage,
        )
        return CandidatePositionResponse(
            id=candidate_position.id,
            candidate_id=candidate_position.candidate_id,
            position_id=candidate_position.position_id,
            stage=candidate_position.stage,
            created_at=candidate_position.created_at.isoformat(),
            updated_at=candidate_position.updated_at.isoformat(),
        )
    except ValueError as e:
        error_msg = str(e)
        if "not found" in error_msg.lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=error_msg,
            ) from e
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=error_msg,
        ) from e


@router.post("/{candidate_id}/archive", response_model=CandidateResponse)
async def archive_candidate(
    candidate_id: int,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> CandidateResponse:
    try:
        candidate = await candidate_service.archive_candidate(session, candidate_id)
        return CandidateResponse(
            id=candidate.id,
            full_name=candidate.full_name,
            email=candidate.email,
            is_archived=candidate.is_archived,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        ) from e
