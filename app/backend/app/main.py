from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.routers import health


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


app = FastAPI(title="backend", lifespan=lifespan)
app.include_router(health.router)
