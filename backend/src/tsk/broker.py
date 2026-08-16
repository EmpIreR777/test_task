import os

import taskiq_fastapi
from loguru import logger
from taskiq import AsyncBroker, InMemoryBroker
from taskiq_redis import RedisAsyncResultBackend, RedisStreamBroker

from src.core.config import settings

mk_broker: AsyncBroker = RedisStreamBroker(
    url=settings.REDIS_URL,
).with_result_backend(
    RedisAsyncResultBackend(redis_url=settings.REDIS_URL),
)

env = os.environ.get('ENVIRONMENT')
if env and env == 'pytest':
    mk_broker = InMemoryBroker()
    logger.debug(f'{mk_broker = }')

taskiq_fastapi.init(mk_broker, 'src.app:app')
