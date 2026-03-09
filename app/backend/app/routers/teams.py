from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel.ext.asyncio.session import AsyncSession

from app.database import get_session
from app.dependencies.auth import get_current_user
from app.exceptions import ConflictError, NotFoundException
from app.models.user import User
from app.schemas.teams import TeamCreate, TeamResponse
from app.services import team_service

router = APIRouter(prefix="/api/teams", tags=["teams"])


@router.get("", response_model=list[TeamResponse])
async def list_teams(
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> list[TeamResponse]:
    teams = await team_service.list_teams(session)
    return [TeamResponse(id=team.id, name=team.name) for team in teams]


@router.post("", response_model=TeamResponse, status_code=status.HTTP_201_CREATED)
async def create_team(
    body: TeamCreate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> TeamResponse:
    try:
        team = await team_service.create_team(session, body.name)
        return TeamResponse(id=team.id, name=team.name)
    except ConflictError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=e.detail,
        ) from e


@router.post("/{team_id}/archive", status_code=status.HTTP_204_NO_CONTENT)
async def archive_team(
    team_id: int,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> None:
    try:
        await team_service.archive_team(session, team_id)
    except NotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=e.detail,
        ) from e
    except ConflictError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=e.detail,
        ) from e
