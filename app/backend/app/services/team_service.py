from sqlalchemy import func
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models.position import Position
from app.models.team import Team


async def list_teams(session: AsyncSession) -> list[Team]:
    statement = select(Team).where(Team.is_archived.is_(False)).order_by(Team.name)
    result = await session.exec(statement)
    return list(result.all())


async def create_team(session: AsyncSession, name: str) -> Team:
    statement = select(Team).where(func.lower(Team.name) == name.lower())
    result = await session.exec(statement)
    existing_team = result.one_or_none()

    if existing_team:
        raise ValueError(f"Team with name '{name}' already exists")

    team = Team(name=name)
    session.add(team)
    await session.commit()
    await session.refresh(team)
    return team


async def delete_team(session: AsyncSession, team_id: int) -> None:
    statement = select(Team).where(Team.id == team_id)
    result = await session.exec(statement)
    team = result.one_or_none()

    if not team:
        raise ValueError(f"Team with id {team_id} not found")

    position_statement = select(Position).where(Position.team_id == team_id)
    position_result = await session.exec(position_statement)
    position = position_result.one_or_none()

    if position:
        raise ValueError(f"Team with id {team_id} is in use by positions")

    await session.delete(team)
    await session.commit()
