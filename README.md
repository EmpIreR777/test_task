# TenderTracker

FastAPI-сервис для управления тендерами: создание, обновление, смена статусов, хранение истории изменений и автоматическая проверка просроченных заявок через background tasks.

## Что включает проект

- FastAPI API с маршрутизаторами для тендеров
- Async SQLAlchemy + PostgreSQL
- Alembic миграции
- Redis + Taskiq для фоновых задач и планировщика
- Docker Compose для локального запуска
- Автотесты через pytest
- Проверка качества кода через uv, mypy, ruff и pre-commit

## Технологии

- Python 3.14
- FastAPI
- SQLAlchemy 2.x
- PostgreSQL 16
- Redis 7
- Taskiq
- Alembic
- uv
- Ruff
- mypy
- pre-commit
- Docker / Docker Compose

## Структура проекта

```text
.
├── backend/
│   ├── src/
│   ├── tests/
│   ├── pyproject.toml
│   ├── Dockerfile
│   ├── Makefile
│   └── README.md
├── docker-compose.dev.yml
├── .env.example
├── README.md
└── Makefile
```

## Быстрый запуск через Docker

```bash
cp .env.example .env
docker compose -f docker-compose.dev.yml up --build -d
```

После запуска:

- API: http://localhost:8000
- Swagger UI: http://localhost:8000/docs
- PostgreSQL: localhost:5432
- Redis: localhost:6379

## Локальная разработка

### 1. Установка зависимостей

```bash
cd backend
uv sync --all-groups
```

### 2. Запуск API

```bash
cd backend
uv run uvicorn src.app:app --host 127.0.0.1 --port 8000 --reload
```

### 3. Запуск background worker и scheduler

В проекте используется Taskiq, и фоновые задачи запускаются вместе с контейнерами Docker Compose.

Для локального запуска через контейнеры:

```bash
docker compose -f docker-compose.dev.yml up --build -d
```

## Тестирование

```bash
cd backend
ENVIRONMENT=pytest uv run pytest -q
```

Также можно запускать тесты из контейнера:

```bash
docker exec backend sh -lc 'cd /backend && ENVIRONMENT=pytest pytest -q'
```

## Проверка качества кода

Проект использует современный набор инструментов для статической проверки и автоформатирования:

```bash
cd backend
uv run mypy src
uv run ruff check .
uv run ruff format --check .
uv run pre-commit run --all-files
```

## Что важно в проекте

- Поддерживаются статусы тендеров и валидация допустимых переходов
- Для каждого изменения сохраняется история в `tender_status_history`
- Просроченные активные тендеры автоматически закрываются фоновым Taskiq-заданием
- Для локального развёртывания используются `.env` переменные и Docker Compose

## API

Основные маршруты:

- `POST /api/v1/tenders` — создать тендер
- `GET /api/v1/tenders` — список тендеров
- `GET /api/v1/tenders/{id}` — получить тендер
- `PATCH /api/v1/tenders/{id}` — обновить тендер
- `PATCH /api/v1/tenders/{id}/status` — изменить статус
- `GET /api/v1/tenders/{id}/history` — история статусов
- `DELETE /api/v1/tenders/{id}` — удалить тендер

## Переменные окружения

Настройки берутся из `.env` и `.env.example`.

Пример:

```env
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=tendertracker
POSTGRES_HOST=backend-db
POSTGRES_PORT=5432

REDIS_HOST=backend-redis
REDIS_PORT=6379

LOG_LEVEL=INFO
```

## Лицензия

Проект распространяется под лицензией MIT. Полный текст лицензии находится в файле [LICENSE](LICENSE).

> Для данного задания лицензия подключена в корне репозитория и явно упомянута в README, чтобы соблюсти требования по подтверждению лицензии.

## Notes

- Используется `uv` как основной менеджер зависимостей и запуска команд.
- `mypy` отвечает за типизацию и статический анализ.
- `ruff` — за линтинг и форматирование.
- `pre-commit` — для автоматического запуска проверок до коммита.