# Task Manager

[![Python](https://img.shields.io/badge/python-3.11-blue)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.101.0-brightgreen)](https://fastapi.tiangolo.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-blue)](https://www.postgresql.org/)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)

## Архитектура и структура проекта

Основные директории и модули:

- **app/main.py** — точка входа FastAPI‑приложения; регистрирует роутеры (`/health`, `/tasks`) и в `lifespan` создаёт таблицы в базе.
- **app/db.py** — настройка подключения к PostgreSQL (`DATABASE_URL`), создание асинхронного `engine`, `AsyncSessionLocal` и `Base`, зависимость `get_db()`.
- **app/models** — SQLAlchemy‑модели:
  - **`task.py`** — модель `Task` и `StatusEnum` (`todo`, `in_progress`, `done`, `overdue`);
  - **`base.py`** — базовый миксин с общими полями (`id`, `created_at`, `updated_at`).
- **app/schemas.py** — Pydantic‑схемы:
  - `TaskCreate`, `TaskUpdate` — входные данные;
  - `TaskOut` — данные, возвращаемые клиенту.
- **app/services/task_service.py** — бизнес‑логика (сервисный слой) для работы с задачами:
  - создание, чтение, обновление, удаление;
  - список с фильтрацией и пагинацией;
  - пересчёт просроченных задач.
- **app/routers** — контроллеры (HTTP‑слой):
  - `health.py` — эндпоинт `/health`;
  - `tasks.py` — все эндпоинты для работы с задачами.
- **app/dependencies.py** — зависимости FastAPI:
  - чтение заголовка `X-User-Id`;
  - сборка `TaskService` из `AsyncSession` и `user_id`.
- **tests/** — тесты: проверка создания задач, бизнес‑правил.

Такое разделение упрощает тестирование бизнес‑логики, изоляцию слоёв и последующую доработку (например, смену БД или добавление новых эндпоинтов).

## Бизнес‑правила

1. **Пользователь работает только со своими задачами**
   - ID пользователя берётся из заголовка `X-User-Id`.
   - При чтении/обновлении/удалении проверяется, что `task.owner_id == user_id`; иначе возвращается ошибка доступа (403) или 404.

2. **Статус `done` требует `due_date`**
   - При создании/обновлении задачи:
     - если статус `done` и `due_date` не задан — выбрасывается `ValueError`, который на уровне API превращается в `422 Unprocessable Entity`.

3. **Просроченные задачи**
   - Задача считается просроченной, если `due_date < now()` и `status != done`.
   - Сервис `recalculate_overdue()`:
     - обновляет флаг `is_overdue`;
     - при просрочке выставляет статус `overdue`;
     - вызывается отдельным эндпоинтом (доступен только «админу»).

## Переменные окружения

Все параметры конфигурации передаются через `.env` (используется и сервисом БД, и бэкендом):

Пример `template.env`:

```env
POSTGRES_USER=task_user
POSTGRES_PASSWORD=task_password
POSTGRES_DB=task_manager

# URL для FastAPI‑приложения (async)
DATABASE_URL=postgresql+asyncpg://task_user:task_password@db:5432/task_manager
```

- Сервис `db` в `docker-compose.yml` читает `POSTGRES_*` для инициализации PostgreSQL.
- Сервис `web` читает `DATABASE_URL` и создаёт асинхронный SQLAlchemy‑engine.

## Установка и запуск через Docker

1. **Создайте `.env` на основе `template.env`** в корне проекта:

   ```bash
   cp template.env .env
   # отредактируйте значения при необходимости
   ```

2. **Соберите и запустите контейнеры**:

   ```bash
   docker compose up --build
   ```

3. После запуска:
   - API доступен по адресу: `http://localhost:8000`
   - Swagger UI: `http://localhost:8000/docs`
   - Health‑check: `http://localhost:8000/health`

## Авторизация

Для всех эндпоинтов работы с задачами требуется заголовок:

```http
X-User-Id: <строковый ID пользователя>
```

- Если заголовок отсутствует — вернётся `401 Unauthorized`.
- Для административного пересчёта просрочек необходим:

  ```http
  X-User-Id: admin
  ```

## Примеры запросов (curl)

### Создание задачи

```bash
curl -X POST "http://localhost:8000/tasks/" \
  -H "Content-Type: application/json" \
  -H "X-User-Id: 1" \
  -d '{
    "title": "Сделать тестовое задание",
    "description": "Реализовать Task Manager на FastAPI",
    "status": "todo",
    "due_date": "2025-12-31T23:59:59+00:00"
  }'
```

### Получение задачи по ID

```bash
curl -X GET "http://localhost:8000/tasks/1" \
  -H "X-User-Id: 1"
```

### Обновление задачи

```bash
curl -X PUT "http://localhost:8000/tasks/1" \
  -H "Content-Type: application/json" \
  -H "X-User-Id: 1" \
  -d '{
    "status": "in_progress"
  }'
```

### Удаление задачи

```bash
curl -X DELETE "http://localhost:8000/tasks/1" \
  -H "X-User-Id: 1"
```

### Список задач с фильтрацией и пагинацией

```bash
curl -X GET "http://localhost:8000/tasks/?status=todo&due_from=2025-01-01T00:00:00&due_to=2025-12-31T23:59:59&limit=10&offset=0" \
  -H "X-User-Id: 1"
```

### Пересчёт просроченных задач (админ)

```bash
curl -X POST "http://localhost:8000/tasks/recalculate_overdue" \
  -H "X-User-Id: admin"
```

Ответ:

```json
{"updated": 3}
```

## Тесты

Если настроены тесты, их можно запускать командой:

```bash
pytest
```

Обычно проверяются:

- успешное создание задачи;
- попытка установить `status="done"` без `due_date`;
- невозможность удалить/прочитать чужую задачу.

## Ограничения и упрощения

- Аутентификация упрощена до заголовка `X-User-Id`.
- Отдельной таблицы пользователей нет, используется строковый `owner_id`.
- Миграции БД могут быть настроены через Alembic, но базовый сценарий опирается на `Base.metadata.create_all()` при старте.
- Логирование и метрики сведены к минимуму.

## Использование ИИ‑инструментов

При выполнении задания использовался **ChatGPT**:

- для генерации начального шаблона FastAPI‑приложения, структуры каталогов и Docker‑конфигурации;
- для подсказок по формулировке README и примерам curl‑запросов.
