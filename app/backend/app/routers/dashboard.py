from fastapi import APIRouter, Depends
from sqlmodel.ext.asyncio.session import AsyncSession

from app.database import get_session
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.schemas.dashboard import DashboardStats
from app.services import dashboard_service

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("/stats", response_model=DashboardStats)
async def get_dashboard_stats(
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> DashboardStats:
    return await dashboard_service.get_dashboard_stats(session)
