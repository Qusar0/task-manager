from datetime import datetime
from typing import Optional, List, Sequence

from fastapi import APIRouter, Depends, HTTPException, Query

from app.services.task_service import TaskService
from app.schemas import TaskCreate, TaskOut, TaskUpdate
from app.models.task import Task
from app.dependencies import get_task_service


router = APIRouter()


@router.post("/", response_model=TaskOut, status_code=201)
async def create_task_endpoint(
    task_in: TaskCreate,
    task_service: TaskService = Depends(get_task_service),
) -> Optional[Task]:
    """Создаёт задачу для текущего пользователя.

    Args:
        task_in (TaskCreate): Описание задачи

    Raises:
        HTTPException: Неверный формат запроса

    Returns:
        Optional[Task]: Созданная задача
    """
    try:
        task = await task_service.create_task(task_in=task_in)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    return task


@router.get("/{task_id}", response_model=TaskOut)
async def get_task_endpoint(
    task_id: int,
    task_service: TaskService = Depends(get_task_service),
) -> Optional[Task]:
    """Получает задачу по ID.

    Args:
        task_id (int): ID задачи

    Raises:
        HTTPException: Задача не найдена (404)
        HTTPException: Доступ запрещён (403)

    Returns:
        Optional[Task]: Полученная задача
    """
    task = await task_service.get_task(task_id)
    if not task:
        raise HTTPException(404, "Задача не найдена")
    if task.owner_id != task_service.user_id:
        raise HTTPException(403, "Доступ запрещён")
    return task


@router.put("/{task_id}", response_model=TaskOut)
async def update_task_endpoint(
    task_id: int,
    data: TaskUpdate,
    task_service: TaskService = Depends(get_task_service),
) -> Optional[Task]:
    """Обновляет задачу по ID.

    Args:
        task_id (int): ID задачи
        data (TaskUpdate): Обновленные данные задачи

    Raises:
        HTTPException: Задача не найдена (404)
        HTTPException: Доступ запрещён (403)
        HTTPException: Неверный формат запроса (422)

    Returns:
        Optional[Task]: Обновленная задача
    """
    task = await task_service.get_task(task_id)
    if not task:
        raise HTTPException(404, "Задача не найдена")
    if task.owner_id != task_service.user_id:
        raise HTTPException(403, "Доступ запрещён")

    try:
        updated = await task_service.update_task(task, data)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    return updated


@router.delete("/{task_id}", status_code=204)
async def delete_task_endpoint(
    task_id: int,
    task_service: TaskService = Depends(get_task_service),
) -> None:
    """Удаляет задачу по ID.

    Args:
        task_id (int): ID задачи

    Raises:
        HTTPException: Задача не найдена (404)
        HTTPException: Доступ запрещён (403)
    """
    task = await task_service.get_task(task_id)
    if not task:
        raise HTTPException(404, "Задача не найдена")
    if task.owner_id != task_service.user_id:
        raise HTTPException(403, "Доступ запрещён")
    await task_service.delete_task(task)


@router.get("/", response_model=List[TaskOut])
async def list_tasks_endpoint(  # noqa: WPS211
    status: Optional[str] = Query(None),
    due_from: Optional[str] = Query(None),
    due_to: Optional[str] = Query(None),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    task_service: TaskService = Depends(get_task_service),
) -> Sequence[Task]:
    """Получает список задач текущего пользователя с возможностью фильтрации.

    Args:
        status (Optional[str]): Статус выполнения. Defaults to Query(None).
        due_from (Optional[str]): Действительна ОТ. Defaults to Query(None).
        due_to (Optional[str]): Действительна ДО. Defaults to Query(None).
        limit (int): Количество записей. Defaults to Query(20, ge=1, le=100).
        offset (int): Номер страницы. Defaults to Query(0, ge=0).

    Returns:
        List[Task]: Отфильтрованные задачи пользователя.
    """
    df = datetime.fromisoformat(due_from) if due_from else None
    dt = datetime.fromisoformat(due_to) if due_to else None

    _, items = await task_service.list_tasks(
        status=status,
        due_from=df,
        due_to=dt,
        limit=limit,
        offset=offset,
    )
    return items


@router.post("/recalculate_overdue")
async def recalc_overdue(task_service: TaskService = Depends(get_task_service)):
    """Пересчитывает просроченные задачи.

    Raises:
        HTTPException: Доступ запрещён (403)
    """
    if task_service.user_id != "admin":
        raise HTTPException(403, "Доступ запрещён")
    updated = await task_service.recalculate_overdue()
    return {"updated": updated}
