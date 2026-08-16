from datetime import UTC, datetime

from fastapi import HTTPException, status
from loguru import logger
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import settings
from src.dao import TenderDAO, TenderStatusHistoryDAO
from src.db.enums import TenderStatus
from src.db.models import Tender, TenderStatusHistory
from src.schemas import TenderCreate, TenderStatusUpdate, TenderUpdate

# Допустимые переходы статусов
ALLOWED_TRANSITIONS: dict[str, set[str]] = {
    TenderStatus.DRAFT: {TenderStatus.ACTIVE, TenderStatus.LOST},
    TenderStatus.ACTIVE: {TenderStatus.WON, TenderStatus.LOST},
    TenderStatus.WON: set(),
    TenderStatus.LOST: set(),
}


class TenderService:
    """Сервис для управления тендерами и их статусами."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_tenders(
        self,
        page: int = 1,
        page_size: int = settings.DEFAULT_PAGE_SIZE,
        query: str | None = None,
        status_filter: str | None = None,
    ) -> tuple[list[Tender], int]:
        """Возвращает пагинированный список тендеров с фильтрацией."""
        query = query.strip() if query else None

        logger.info(f'Получение списка тендеров. page={page}, page_size={page_size}, query={query!r}')

        search_filter = None
        if query:
            search_filter = or_(
                Tender.title.ilike(f'%{query}%'),
                Tender.customer.ilike(f'%{query}%'),
            )
        if status_filter:
            status_cond = Tender.status == status_filter
            search_filter = status_cond if search_filter is None else search_filter & status_cond

        tenders, total = await TenderDAO.paginate(
            self.session,
            page=page,
            page_size=page_size,
            filters=search_filter,
            order_by=Tender.created_at.desc(),
        )

        logger.info(f'Найдено {len(tenders)} тендеров, всего: {total}')
        return tenders, total

    async def get_tender(self, tender_id: int) -> Tender:
        """Возвращает тендер по ID или выбрасывает 404."""
        logger.info(f'Поиск тендера с ID: {tender_id}')
        tender = await TenderDAO.find_one_or_none_by_id(tender_id, self.session)
        if not tender:
            logger.warning(f'Тендер с ID {tender_id} не найден')
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Tender not found')
        logger.info(f'Тендер с ID {tender_id} найден: {tender.title}')
        return tender

    async def create_tender(self, payload: TenderCreate) -> Tender:
        """Создаёт новый тендер со статусом 'draft'."""
        logger.info(f'Создание тендера: {payload.title}')
        tender = await TenderDAO.add(
            session=self.session,
            values={
                'title': payload.title,
                'description': payload.description,
                'customer': payload.customer,
                'budget': payload.budget,
                'deadline': payload.deadline,
                'status': TenderStatus.DRAFT,
            },
        )
        await self.session.refresh(tender)
        logger.info(f'Тендер создан. ID: {tender.id}')
        return tender

    async def update_tender(self, tender_id: int, payload: TenderUpdate) -> Tender:
        """Обновляет поля тендера (без изменения статуса)."""
        logger.info(f'Обновление тендера с ID: {tender_id}')
        tender = await self.get_tender(tender_id)

        update_data = payload.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(tender, field, value)

        await self.session.flush()
        await self.session.refresh(tender)
        logger.info(f'Тендер с ID {tender_id} успешно обновлен')
        return tender

    async def change_status(self, tender_id: int, payload: TenderStatusUpdate) -> Tender:
        """Изменяет статус тендера и логирует изменение в историю."""
        logger.info(f'Изменение статуса тендера {tender_id} на {payload.status}')
        tender = await self.get_tender(tender_id)

        new_status = payload.status
        if new_status not in TenderStatus.__members__.values():
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail=f'Invalid status: {new_status}. Allowed: {[s.value for s in TenderStatus]}',
            )

        old_status = tender.status
        if old_status == new_status:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f'Tender is already in status {new_status}',
            )

        allowed = ALLOWED_TRANSITIONS.get(old_status, set())
        if new_status not in allowed:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f'Invalid transition from {old_status} to {new_status}',
            )

        # Обновляем статус
        tender.status = new_status
        await self.session.flush()

        # Логируем изменение в историю
        await TenderStatusHistoryDAO.add(
            session=self.session,
            values={
                'tender_id': tender_id,
                'from_status': old_status,
                'to_status': new_status,
                'changed_by': payload.changed_by,
                'reason': payload.reason,
            },
        )

        await self.session.refresh(tender)
        logger.info(f'Статус тендера {tender_id} изменен: {old_status} -> {new_status}')
        return tender

    async def list_history(
        self,
        tender_id: int,
        page: int = 1,
        page_size: int = settings.DEFAULT_PAGE_SIZE,
    ) -> tuple[list[TenderStatusHistory], int]:
        """Возвращает историю изменений статуса тендера."""
        logger.info(f'Получение истории статусов тендера {tender_id}')
        await self.get_tender(tender_id)

        history, total = await TenderStatusHistoryDAO.paginate(
            self.session,
            page=page,
            page_size=page_size,
            filters={'tender_id': tender_id},
            order_by=TenderStatusHistory.created_at.desc(),
        )

        logger.info(f'Найдено {len(history)} записей истории, всего: {total}')
        return history, total

    async def close_expired_tenders(self) -> int:
        """Переводит просроченные active тендеры в статус lost."""
        now = datetime.now(UTC)
        result = await self.session.execute(
            select(Tender)
            .where(Tender.deadline.is_not(None))
            .where(Tender.status == TenderStatus.ACTIVE)
            .where(Tender.deadline < now),
        )
        expired_tenders = result.scalars().all()

        updated_count = 0
        for tender in expired_tenders:
            tender.status = TenderStatus.LOST
            await TenderStatusHistoryDAO.add(
                session=self.session,
                values={
                    'tender_id': tender.id,
                    'from_status': TenderStatus.ACTIVE,
                    'to_status': TenderStatus.LOST,
                    'changed_by': 'scheduler',
                    'reason': 'Дедлайн истёк (автоматически)',
                },
            )
            updated_count += 1

        if expired_tenders:
            await self.session.flush()

        logger.info(f'Проверка дедлайнов: найдено {len(expired_tenders)}, обновлено {updated_count}')
        return updated_count

    async def delete_tender(self, tender_id: int) -> None:
        """Удаляет тендер (история удалится каскадно)."""
        logger.info(f'Удаление тендера с ID: {tender_id}')
        tender = await self.get_tender(tender_id)
        await self.session.delete(tender)
        await self.session.flush()
        logger.info(f'Тендер с ID {tender_id} удален')
