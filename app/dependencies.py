from typing import Optional
from fastapi import Depends, Header, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.services.task_service import TaskService


def get_current_user(x_user_id: Optional[str] = Header(None)) -> str:
    """Получает ID пользователя.

    Args:
        x_user_id (Optional[str]): ID пользователя в заголовке. Defaults to Header(None).

    Raises:
        HTTPException: Отсутствует авторизация
    """
    if not x_user_id:
        raise HTTPException(status_code=401, detail="X-User-Id header required")
    return x_user_id


def get_task_service(
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user),
) -> TaskService:
    """Возвращает TaskService с привязанным db."""
    return TaskService(db, user_id)
