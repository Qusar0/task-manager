import pytest
from unittest.mock import AsyncMock
from datetime import datetime, timedelta, timezone

from app.services.task_service import TaskService
from app.models.task import Task, StatusEnum
from app.schemas import TaskCreate, TaskUpdate


@pytest.fixture
def mock_db():
    """Создаём мок асинхронной сессии."""
    db = AsyncMock()
    db.commit = AsyncMock()
    db.refresh = AsyncMock()
    db.delete = AsyncMock()
    db.execute = AsyncMock()
    return db


@pytest.fixture
def task_service(mock_db):  # noqa: WPS442
    """Создаём TaskService с мок-сессией и фиктивным пользователем."""
    return TaskService(db=mock_db, user_id="user1")


@pytest.fixture
def sample_task():
    """Возвращает пример задачи."""
    return Task(
        id=1,
        owner_id="user1",
        title="Sample Task",
        description="Описание задачи",
        status=StatusEnum.TODO,
        due_date=datetime.now(timezone.utc) + timedelta(days=1),
        is_overdue=False,
    )


@pytest.fixture
def overdue_task():
    """Возвращает просроченную задачу."""
    now = datetime.now(timezone.utc)
    return Task(
        id=2,
        owner_id="user1",
        title="Overdue Task",
        status=StatusEnum.TODO,
        due_date=now - timedelta(days=1),
        is_overdue=False,
    )


@pytest.fixture
def future_task():
    """Возвращает задачу с дедлайном в будущем."""
    now = datetime.now(timezone.utc)
    return Task(
        id=3,
        owner_id="user1",
        title="Future Task",
        status=StatusEnum.TODO,
        due_date=now + timedelta(days=2),
        is_overdue=False,
    )


@pytest.fixture
def task_create_payload():
    """Возвращает payload для создания задачи."""
    return TaskCreate(
        title="New Task",
        description="Новая задача",
        status=StatusEnum.TODO,
        due_date=datetime.now(timezone.utc) + timedelta(days=1),
    )


@pytest.fixture
def task_update_payload():
    """Возвращает payload для обновления задачи."""
    return TaskUpdate(
        title="Updated Task",
        description="Обновлённое описание",
        status=StatusEnum.DONE,
        due_date=datetime.now(timezone.utc) + timedelta(days=1),
    )
