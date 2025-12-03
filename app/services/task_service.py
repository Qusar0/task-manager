from typing import Optional, Tuple, Sequence
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.task import Task, StatusEnum
from app.schemas import TaskCreate, TaskUpdate


class TaskService:
    """Асинхронный сервис для управления задачами."""

    def __init__(self, db: AsyncSession, user_id: str):
        """
        Инициализация сервиса.

        Args:
            db (AsyncSession): Асинхронная сессия БД
            user_id (str): ID текущего пользователя
        """
        self.db = db
        self.user_id = user_id

    async def create_task(self, task_in: TaskCreate) -> Task:
        """
        Создаёт новую задачу.

        Args:
            task_in (TaskCreate): Данные создаваемой задачи

        Raises:
            ValueError: Если статус DONE без due_date

        Returns:
            Task: Созданная задача
        """
        if task_in.status == StatusEnum.DONE and not task_in.due_date:
            raise ValueError("Статус 'done' требует указания due_date")

        task = Task(
            owner_id=self.user_id,
            title=task_in.title,
            description=task_in.description,
            status=task_in.status,
            due_date=task_in.due_date,
        )

        self.db.add(task)
        await self.db.commit()
        await self.db.refresh(task)

        return task

    async def get_task(self, task_id: int) -> Optional[Task]:
        """
        Получает задачу по ID.

        Args:
            task_id (int): ID задачи

        Returns:
            Optional[Task]: Найденная задача или None
        """
        result = await self.db.execute(
            select(Task).where(Task.id == task_id),
        )
        return result.scalar_one_or_none()

    async def update_task(self, task: Task, data: TaskUpdate) -> Task:
        """
        Обновляет существующую задачу.

        Args:
            task (Task): Объект задачи
            data (TaskUpdate): Новые данные

        Raises:
            ValueError: Если статус DONE без due_date

        Returns:
            Task: Обновлённая задача
        """
        if data.status == StatusEnum.DONE:
            due = data.due_date if data.due_date is not None else task.due_date
            if not due:
                raise ValueError("Статус 'done' требует указания due_date")

        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(task, field, value)

        await self.db.commit()
        await self.db.refresh(task)

        return task

    async def delete_task(self, task: Task):
        """
        Удаляет задачу.

        Args:
            task (Task): Задача для удаления
        """
        await self.db.delete(task)
        await self.db.commit()

    async def list_tasks(  # noqa: WPS211
        self,
        status: Optional[StatusEnum] = None,
        due_from: Optional[datetime] = None,
        due_to: Optional[datetime] = None,
        limit: int = 20,
        offset: int = 0,
    ) -> Tuple[int, Sequence[Task]]:
        """
        Возвращает список задач с фильтрами и пагинацией.

        Args:
            status (Optional[StatusEnum]): Фильтр по статусу
            due_from (Optional[datetime]): Дата ОТ
            due_to (Optional[datetime]): Дата ДО
            limit (int): Количество записей
            offset (int): Смещение

        Returns:
            Tuple[int, List[Task]]: (общее количество, список задач)
        """
        q = select(Task).where(Task.owner_id == self.user_id)

        if status:
            q = q.where(Task.status == status)
        if due_from:
            q = q.where(Task.due_date >= due_from)
        if due_to:
            q = q.where(Task.due_date <= due_to)

        total_result = await self.db.execute(q)
        total = len(total_result.scalars().all())

        items_result = await self.db.execute(
            q.order_by(Task.created_at.desc()).offset(offset).limit(limit),
        )
        items = items_result.scalars().all()

        return total, items

    async def recalculate_overdue(self) -> int:
        """
        Пересчитывает просроченные задачи.

        Returns:
            int: Количество обновленных задач
        """
        now = datetime.now(timezone.utc)

        result = await self.db.execute(
            select(Task).where(Task.status != StatusEnum.DONE),
        )
        tasks = result.scalars().all()

        updated = 0

        for task in tasks:
            is_over = False
            if task.due_date is not None:
                if task.due_date.tzinfo is None:
                    due_date_utc = task.due_date.replace(tzinfo=timezone.utc)
                else:
                    due_date_utc = task.due_date
                is_over = due_date_utc < now

            if task.is_overdue != is_over:
                task.is_overdue = is_over

                if is_over:
                    task.status = StatusEnum.OVERDUE

                updated += 1
                self.db.add(task)

        if updated:
            await self.db.commit()

        return updated
