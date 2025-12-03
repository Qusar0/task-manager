from typing import Optional
from datetime import datetime, timezone
from pydantic import BaseModel, Field, validator
from app.models.task import StatusEnum


class TaskCreate(BaseModel):
    """Схема для создания новой задачи."""

    title: str = Field(
        ...,
        min_length=1,
        description="Название задачи. Минимум 1 символ.",
    )
    description: Optional[str] = Field(
        None,
        description="Описание задачи.",
    )
    due_date: Optional[datetime] = Field(
        None,
        description="Дедлайн задачи.",
    )
    status: Optional[StatusEnum] = Field(
        StatusEnum.TODO,
        description="Статус задачи.",
    )

    @validator("due_date", pre=True, always=True)
    def ensure_due_date_utc(cls, v):
        """Гарантирует, что due_date в UTC."""
        if v is None:
            return v
        if isinstance(v, str):
            v = datetime.fromisoformat(v)
        if v.tzinfo is None:
            v = v.replace(tzinfo=timezone.utc)
        return v


class TaskUpdate(BaseModel):
    """Схема для обновления существующей задачи."""

    title: Optional[str] = Field(
        None,
        description="Новое название задачи.",
    )
    description: Optional[str] = Field(
        None,
        description="Новое описание задачи.",
    )
    due_date: Optional[datetime] = Field(
        None,
        description="Новый дедлайн задачи.",
    )
    status: Optional[StatusEnum] = Field(
        None,
        description="Новый статус задачи.",
    )

    @validator("due_date", pre=True, always=True)
    def ensure_due_date_utc(cls, v):
        """Гарантирует, что due_date в UTC."""
        if v is None:
            return v
        if isinstance(v, str):
            v = datetime.fromisoformat(v)
        if v.tzinfo is None:
            v = v.replace(tzinfo=timezone.utc)
        return v


class TaskOut(BaseModel):
    """Схема для возврата задачи пользователю."""

    id: int = Field(description="ID задачи.")
    owner_id: str = Field(description="ID владельца задачи.")
    title: str = Field(description="Название задачи.")
    description: Optional[str] = Field(None, description="Описание задачи.")
    status: StatusEnum = Field(description="Статус задачи.")
    due_date: Optional[datetime] = Field(None, description="Дедлайн задачи.")
    is_overdue: bool = Field(description="Просрочена ли задача.")
    created_at: datetime = Field(description="Дата создания задачи.")
    updated_at: datetime = Field(description="Дата последнего обновления задачи.")

    class Config:
        """Включает ORM режим для совместимости с моделями SQLAlchemy."""

        orm_mode = True
