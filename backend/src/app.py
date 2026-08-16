from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.admin_panel.admin import register_admin
from src.core.config import settings
from src.core.logging_config import setup_logger
from src.db.session_make import async_engine
from src.routers import router
from src.tsk import (
    broker,  # noqa: F401 - инициализирует taskiq_fastapi
    tasks,  # noqa: F401 - регистрирует задачи
)

logger = setup_logger(
    log_dir='logs',
    log_file='debug.log',
    log_level=settings.LOG_LEVEL,
    rotation='100 MB',
    retention='10 days',
)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Логирует запуск и остановку приложения."""
    try:
        logger.info(f'Запуск приложения: {settings.API_TITLE}.')
        yield
    finally:
        logger.info(f'Приложение {settings.API_TITLE} остановлено.')


app = FastAPI(
    lifespan=lifespan, version=settings.API_VERSION, title=settings.API_TITLE, description=settings.API_DESCRIPTION
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        'http://localhost:3000',
        'http://127.0.0.1:3000',
    ],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)

app.include_router(router)

register_admin(app, async_engine)
