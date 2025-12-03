import os
from collections.abc import AsyncGenerator
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import declarative_base


DATABASE_URL = os.getenv("DATABASE_URL", '')

engine = create_async_engine(
    DATABASE_URL,
    future=True,
    echo=False,
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False,
    class_=AsyncSession,
)

Base = declarative_base()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Асинхронный зависимый генератор для получения сессии БД.

    Yields:
        Iterator[AsyncGenerator[AsyncSession, None]]: Асинхронная сессия БД
    """
    async with AsyncSessionLocal() as session:
        yield session
