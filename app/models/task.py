from sqlalchemy import Column, String, Text, DateTime, Enum, Boolean
import enum
from app.models.base import BaseModelMixin
from app.db import Base


class StatusEnum(str, enum.Enum):
    """Перечисление статусов задачи."""

    TODO = "todo"
    IN_PROGRESS = "in_progress"
    DONE = "done"
    OVERDUE = "overdue"


class Task(Base, BaseModelMixin):
    """Модель задачи."""

    __tablename__ = "tasks"

    owner_id = Column(String, index=True, nullable=False)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    status = Column(Enum(StatusEnum), default=StatusEnum.TODO, nullable=False)
    due_date = Column(DateTime(timezone=True), nullable=True)
    is_overdue = Column(Boolean, default=False, nullable=False)
