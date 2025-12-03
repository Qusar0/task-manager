import pytest
from unittest.mock import AsyncMock, Mock

from app.models.task import StatusEnum
from app.schemas import TaskUpdate, TaskCreate


@pytest.mark.asyncio
async def test_create_task_success(task_service, task_create_payload):
    """Тест успешного создания задачи."""
    task = await task_service.create_task(task_create_payload)
    assert task.title == task_create_payload.title
    assert task.status == task_create_payload.status
    task_service.db.add.assert_called_once_with(task)
    task_service.db.commit.assert_awaited()
    task_service.db.refresh.assert_awaited()


@pytest.mark.asyncio
async def test_create_task_done_without_due_date_raises(task_service):
    """Тест создания задачи со статусом DONE без due_date."""
    invalid_payload = TaskCreate(title="Task", status=StatusEnum.DONE, due_date=None)
    with pytest.raises(ValueError):
        await task_service.create_task(invalid_payload)


@pytest.mark.asyncio
async def test_get_task_found(task_service, sample_task):
    """Тест успешного получения задачи по ID."""
    execute_result_mock = Mock()
    execute_result_mock.scalar_one_or_none.return_value = sample_task

    task_service.db.execute = AsyncMock(return_value=execute_result_mock)

    task = await task_service.get_task(sample_task.id)

    assert task == sample_task
    task_service.db.execute.assert_called_once()
    execute_result_mock.scalar_one_or_none.assert_called_once()


@pytest.mark.asyncio
async def test_get_task_not_found(task_service):
    """Тест получения несуществующей задачи по ID."""
    task_service.db.execute.return_value.scalar_one_or_none = Mock(return_value=None)
    task = await task_service.get_task(999)
    assert task is None


@pytest.mark.asyncio
async def test_update_task_success(task_service, sample_task, task_update_payload):
    """Тест успешного обновления задачи."""
    updated_task = await task_service.update_task(sample_task, task_update_payload)
    assert updated_task.title == task_update_payload.title
    assert updated_task.status == task_update_payload.status
    task_service.db.commit.assert_awaited()
    task_service.db.refresh.assert_awaited()


@pytest.mark.asyncio
async def test_update_task_done_without_due_date_raises(task_service, sample_task):
    """Тест обновления задачи со статусом DONE без due_date."""
    payload = TaskUpdate(status=StatusEnum.DONE, due_date=None)
    sample_task.due_date = None
    with pytest.raises(ValueError):
        await task_service.update_task(sample_task, payload)


@pytest.mark.asyncio
async def test_delete_task(task_service, sample_task):
    """Тест успешного удаления задачи."""
    await task_service.delete_task(sample_task)
    task_service.db.delete.assert_awaited_with(sample_task)
    task_service.db.commit.assert_awaited()


@pytest.mark.asyncio
async def test_list_tasks(task_service, sample_task, overdue_task, future_task):
    """Тест получения списка задач."""
    tasks = [sample_task, overdue_task, future_task]

    execute_result_mock = Mock()
    scalars_mock = Mock()
    scalars_mock.all.return_value = tasks
    execute_result_mock.scalars.return_value = scalars_mock

    task_service.db.execute = AsyncMock(return_value=execute_result_mock)

    total, items = await task_service.list_tasks()

    assert total == 3
    assert len(items) == 3


@pytest.mark.asyncio
async def test_recalculate_overdue(task_service, sample_task):
    """Тест recalculate_overdue."""
    execute_result_mock = Mock()
    scalars_mock = Mock()
    scalars_mock.all.return_value = [sample_task]
    execute_result_mock.scalars.return_value = scalars_mock

    task_service.db.execute = AsyncMock(return_value=execute_result_mock)

    updated_count = await task_service.recalculate_overdue()
    assert updated_count >= 0
    task_service.db.execute.assert_called_once()
    scalars_mock.all.assert_called_once()


@pytest.mark.asyncio
async def test_recalculate_overdue_none_updated(task_service, future_task):
    """Тест пересчёта просроченных задач, когда нет изменений."""
    execute_result_mock = Mock()
    scalars_mock = Mock()
    scalars_mock.all.return_value = [future_task]
    execute_result_mock.scalars.return_value = scalars_mock
    task_service.db.execute = AsyncMock(return_value=execute_result_mock)

    updated = await task_service.recalculate_overdue()
    assert updated == 0
    assert future_task.is_overdue is False
