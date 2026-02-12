from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel.ext.asyncio.session import AsyncSession

from app.database import get_session
from app.dependencies.auth import get_current_user
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
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e),
        ) from e


@router.delete("/{team_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_team(
    team_id: int,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> None:
    try:
        await team_service.delete_team(session, team_id)
    except ValueError as e:
        error_msg = str(e)
        if "not found" in error_msg:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=error_msg,
            ) from e
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=error_msg,
        ) from e
