from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from src.core.config import settings
from src.db.session_make import get_db_session
from src.schemas import (
    PaginatedHistoryResponse,
    PaginatedTenderResponse,
    TenderCreate,
    TenderItem,
    TenderStatusHistoryItem,
    TenderStatusUpdate,
    TenderUpdate,
)
from src.services.tender_service import TenderService

router = APIRouter(tags=['Tenders'])


@router.get('/tenders', response_model=PaginatedTenderResponse, summary='Пагинированный список тендеров')
async def list_tenders_view(
    page: int = 1,
    query: str | None = None,
    status_filter: str | None = None,
    session: AsyncSession = Depends(get_db_session),
) -> PaginatedTenderResponse:
    effective_page_size = settings.DEFAULT_PAGE_SIZE
    service = TenderService(session)

    items, total = await service.list_tenders(
        page=page,
        page_size=effective_page_size,
        query=query,
        status_filter=status_filter,
    )

    total_pages = (total + effective_page_size - 1) // effective_page_size

    return PaginatedTenderResponse(
        items=[TenderItem.model_validate(tender) for tender in items],
        page=page,
        page_size=effective_page_size,
        total=total,
        total_pages=total_pages,
    )


@router.post('/tenders', response_model=TenderItem, status_code=status.HTTP_201_CREATED, summary='Создать тендер')
async def create_tender_view(
    payload: TenderCreate,
    session: AsyncSession = Depends(get_db_session),
) -> TenderItem:
    service = TenderService(session)
    tender = await service.create_tender(payload)
    return TenderItem.model_validate(tender)


@router.get('/tenders/{tender_id}', response_model=TenderItem, summary='Получить тендер по ID')
async def get_tender_view(tender_id: int, session: AsyncSession = Depends(get_db_session)) -> TenderItem:
    service = TenderService(session)
    tender = await service.get_tender(tender_id)
    return TenderItem.model_validate(tender)


@router.patch('/tenders/{tender_id}', response_model=TenderItem, summary='Обновить данные тендера')
async def update_tender_view(
    tender_id: int,
    payload: TenderUpdate,
    session: AsyncSession = Depends(get_db_session),
) -> TenderItem:
    service = TenderService(session)
    tender = await service.update_tender(tender_id, payload)
    return TenderItem.model_validate(tender)


@router.patch('/tenders/{tender_id}/status', response_model=TenderItem, summary='Изменить статус тендера')
async def change_tender_status_view(
    tender_id: int,
    payload: TenderStatusUpdate,
    session: AsyncSession = Depends(get_db_session),
) -> TenderItem:
    service = TenderService(session)
    tender = await service.change_status(tender_id, payload)
    return TenderItem.model_validate(tender)


@router.get(
    '/tenders/{tender_id}/history',
    response_model=PaginatedHistoryResponse,
    summary='История изменений статуса тендера',
)
async def list_tender_history_view(
    tender_id: int,
    page: int = 1,
    session: AsyncSession = Depends(get_db_session),
) -> PaginatedHistoryResponse:
    effective_page_size = settings.DEFAULT_PAGE_SIZE
    service = TenderService(session)

    items, total = await service.list_history(
        tender_id=tender_id,
        page=page,
        page_size=effective_page_size,
    )

    total_pages = (total + effective_page_size - 1) // effective_page_size

    return PaginatedHistoryResponse(
        items=[TenderStatusHistoryItem.model_validate(item) for item in items],
        page=page,
        page_size=effective_page_size,
        total=total,
        total_pages=total_pages,
    )


@router.delete('/tenders/{tender_id}', status_code=status.HTTP_204_NO_CONTENT, summary='Удалить тендер')
async def delete_tender_view(tender_id: int, session: AsyncSession = Depends(get_db_session)) -> None:
    service = TenderService(session)
    await service.delete_tender(tender_id)
