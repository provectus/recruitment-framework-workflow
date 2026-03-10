from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routers import (
    auth,
    candidates,
    dashboard,
    documents,
    evaluations,
    health,
    position_rubrics,
    positions,
    rubric_templates,
    teams,
    users,
)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    yield


app = FastAPI(title="Lauter API", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "X-Request-ID"],
)

app.include_router(health.router)
app.include_router(auth.router)
app.include_router(dashboard.router)
app.include_router(teams.router)
app.include_router(positions.router)
app.include_router(candidates.router)
app.include_router(users.router)
app.include_router(documents.router)
app.include_router(rubric_templates.router)
app.include_router(position_rubrics.router)
app.include_router(evaluations.router)
