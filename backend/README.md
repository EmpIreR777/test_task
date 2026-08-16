# TenderTracker Backend

Backend-часть сервиса для управления тендерами и их статусами.

## Стек

- Python 3.14
- FastAPI
- SQLAlchemy 2.x + asyncpg
- PostgreSQL 16
- Redis 7
- Taskiq
- Alembic
- uv
- Ruff
- mypy
- pre-commit

## Запуск

```bash
cd backend
uv sync --all-groups
uv run uvicorn src.app:app --host 127.0.0.1 --port 8000 --reload
```

## Тесты

```bash
cd backend
ENVIRONMENT=pytest uv run pytest -q
```

## Проверки качества

```bash
cd backend
uv run mypy src
uv run ruff check .
uv run ruff format --check .
uv run pre-commit run --all-files
```

## Основные возможности

- создание и обновление тендеров
- смена статусов с валидацией переходов
- хранение истории статусов
- автоматическая закрытие просроченных тендеров через Taskiq
- работа через Docker Compose и Redis