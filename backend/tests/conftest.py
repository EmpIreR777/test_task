import asyncio
import logging
from collections.abc import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

import src.db.session_make as session_make_module

from src.app import app
from src.core.config import settings
from src.db.session_make import get_db_session


@pytest.fixture(scope='session')
def event_loop() -> asyncio.AbstractEventLoop:
    """Создание event loop для сессии тестов."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    yield loop
    loop.close()


@pytest_asyncio.fixture
async def async_session_maker() -> AsyncGenerator[async_sessionmaker[AsyncSession]]:
    """Фабрика сессий, работающих в рамках одной транзакции с откатом после теста."""
    test_engine = create_async_engine(
        url=settings.SQLALCHEMY_DB_URL,
        echo=False,
        future=True,
        pool_pre_ping=True,
    )

    async with test_engine.connect() as connection:
        outer_transaction = await connection.begin()

        async_session_factory = async_sessionmaker(
            bind=connection,
            class_=AsyncSession,
            autoflush=False,
            expire_on_commit=False,
            join_transaction_mode='create_savepoint',
        )

        session_make_module.async_session_maker = async_session_factory

        yield async_session_factory

        await outer_transaction.rollback()

    await test_engine.dispose()


@pytest_asyncio.fixture
async def db_session(async_session_maker: async_sessionmaker[AsyncSession]) -> AsyncGenerator[AsyncSession]:
    """Создание сессии БД для каждого теста."""
    async with async_session_maker() as session:
        yield session


@pytest_asyncio.fixture
async def client(
    async_session_maker: async_sessionmaker[AsyncSession],
) -> AsyncGenerator[AsyncClient]:
    """Создание тестового HTTP клиента."""

    async def override_get_db_session() -> AsyncGenerator[AsyncSession]:
        async with async_session_maker() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    app.dependency_overrides[get_db_session] = override_get_db_session

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url='http://test') as test_client:
        yield test_client

    app.dependency_overrides.clear()


@pytest.fixture(autouse=True)
def disable_logging() -> None:
    """Отключение логирования во время тестов."""
    logging.disable(logging.CRITICAL)