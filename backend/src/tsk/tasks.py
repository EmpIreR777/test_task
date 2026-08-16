from loguru import logger

import src.db.session_make as session_make
from src.services.tender_service import TenderService
from src.tsk.broker import mk_broker


@mk_broker.task(schedule=[{'cron': '0 */6 * * *'}])
async def check_expired_tenders() -> int:
    """Проверяет просроченные active тендеры и переводит их в status=lost."""
    async with session_make.async_session_maker() as session:
        try:
            service = TenderService(session)
            updated_count = await service.close_expired_tenders()
            await session.commit()
            logger.info('Taskiq: checked expired tenders, updated %s', updated_count)
            return updated_count
        except Exception:
            await session.rollback()
            logger.exception('Taskiq: failed to check expired tenders')
            raise
