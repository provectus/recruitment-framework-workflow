from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.database import get_session
from app.dependencies.auth import get_current_user
from app.models.candidate import Candidate
from app.models.candidate_position import CandidatePosition
from app.models.team import Team
from app.models.user import User
from app.schemas.positions import (
    CandidateStageItem,
    PaginatedPositions,
    PositionCreate,
    PositionDetailResponse,
    PositionListItem,
    PositionResponse,
    PositionUpdate,
)
from app.services import position_service

router = APIRouter(prefix="/api/positions", tags=["positions"])


@router.get("", response_model=PaginatedPositions)
async def list_positions(
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    status: str | None = Query(default=None),
    team_id: int | None = Query(default=None),
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> PaginatedPositions:
    items, total = await position_service.list_positions(
        session, offset, limit, status, team_id
    )
    return PaginatedPositions(
        items=[PositionListItem(**item) for item in items],
        total=total,
        offset=offset,
        limit=limit,
    )


@router.post("", response_model=PositionResponse, status_code=status.HTTP_201_CREATED)
async def create_position(
    body: PositionCreate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> PositionResponse:
    try:
        position = await position_service.create_position(
            session,
            body.title,
            body.team_id,
            body.hiring_manager_id,
            body.requirements,
        )
        return PositionResponse(
            id=position.id,
            title=position.title,
            requirements=position.requirements,
            status=position.status,
            team_id=position.team_id,
            hiring_manager_id=position.hiring_manager_id,
            is_archived=position.is_archived,
        )
    except ValueError as e:
        error_msg = str(e)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=error_msg,
        ) from e


@router.get("/{position_id}", response_model=PositionDetailResponse)
async def get_position(
    position_id: int,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> PositionDetailResponse:
    position = await position_service.get_position(session, position_id)
    if position is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Position not found",
        )

    team = await session.get(Team, position.team_id)
    hiring_manager = await session.get(User, position.hiring_manager_id)

    candidates_stmt = (
        select(CandidatePosition, Candidate)
        .join(Candidate, CandidatePosition.candidate_id == Candidate.id)
        .where(CandidatePosition.position_id == position_id)
    )
    candidates_result = await session.exec(candidates_stmt)
    candidates_rows = candidates_result.all()

    candidates = [
        CandidateStageItem(
            candidate_id=row.Candidate.id,
            candidate_name=row.Candidate.full_name,
            candidate_email=row.Candidate.email,
            stage=row.CandidatePosition.stage,
        )
        for row in candidates_rows
    ]

    return PositionDetailResponse(
        id=position.id,
        title=position.title,
        requirements=position.requirements,
        status=position.status,
        team_id=position.team_id,
        team_name=team.name,
        hiring_manager_id=position.hiring_manager_id,
        hiring_manager_name=hiring_manager.full_name,
        is_archived=position.is_archived,
        candidates=candidates,
        created_at=position.created_at.isoformat(),
        updated_at=position.updated_at.isoformat(),
    )


@router.patch("/{position_id}", response_model=PositionResponse)
async def update_position(
    position_id: int,
    body: PositionUpdate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> PositionResponse:
    try:
        position = await position_service.update_position(
            session,
            position_id,
            body.title,
            body.requirements,
            body.team_id,
            body.hiring_manager_id,
            body.status,
        )
        return PositionResponse(
            id=position.id,
            title=position.title,
            requirements=position.requirements,
            status=position.status,
            team_id=position.team_id,
            hiring_manager_id=position.hiring_manager_id,
            is_archived=position.is_archived,
        )
    except ValueError as e:
        error_msg = str(e)
        if "not found" in error_msg.lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=error_msg,
            ) from e
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=error_msg,
        ) from e


@router.post("/{position_id}/archive", response_model=PositionResponse)
async def archive_position(
    position_id: int,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> PositionResponse:
    try:
        position = await position_service.archive_position(session, position_id)
        return PositionResponse(
            id=position.id,
            title=position.title,
            requirements=position.requirements,
            status=position.status,
            team_id=position.team_id,
            hiring_manager_id=position.hiring_manager_id,
            is_archived=position.is_archived,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        ) from e
