from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.db import engine, Base
from app.routers import tasks, health


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan приложение: создание таблиц при старте."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield


app = FastAPI(
    title="Task Manager API",
    description="Сервис управления задачами.",
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(health.router, prefix="/health", tags=["health"])
app.include_router(tasks.router, prefix="/tasks", tags=["tasks"])
