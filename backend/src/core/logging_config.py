import logging
import os
import sys
from pathlib import Path
from types import FrameType
from typing import Any

from loguru import logger


class InterceptHandler(logging.Handler):
    """Перенаправляет стандартные логи Python в loguru."""

    def emit(self, record: logging.LogRecord) -> None:
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = str(record.levelno)

        frame: FrameType | None = logging.currentframe()
        depth = 2
        while frame is not None and frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(level, record.getMessage())


def setup_logger(
    log_dir: str = 'logs',
    log_file: str = 'app.log',
    log_level: str = 'INFO',
    rotation: str = '100 MB',
    retention: str = '7 days',
) -> Any:
    """Настройка логгера: консоль + файл с ротацией."""

    logger.remove()

    Path(log_dir).mkdir(exist_ok=True)
    log_path = os.path.join(log_dir, log_file)

    form = (
        '<green>{time:YYYY-MM-DD HH:mm:ss}</green> | '
        '<level>{level: <8}</level> | <cyan>{name}</cyan>:'
        '<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>'
    )
    logger.add(
        sys.stdout,
        format=form,
        level=log_level,
        colorize=True,
        enqueue=True,
        backtrace=True,
    )

    logger.add(
        log_path,
        format='{time:YYYY-MM-DD HH:mm:ss} | {level: <8} \
            | {name}:{function}:{line} - {message}',
        level=log_level,
        rotation=rotation,
        retention=retention,
        enqueue=True,
        compression='zip',
    )

    logging.basicConfig(
        handlers=[InterceptHandler()],
        level=log_level,
        force=True,
    )

    logging.getLogger('uvicorn.access').disabled = True
    logging.getLogger('uvicorn.error').setLevel(log_level)
    logging.getLogger('fastapi').setLevel(log_level)
    logging.getLogger('sqlalchemy.engine').setLevel(logging.WARNING if log_level == 'INFO' else log_level)
    logging.getLogger('alembic').setLevel(log_level)
    logging.getLogger('asyncio').setLevel(log_level)

    return logger
