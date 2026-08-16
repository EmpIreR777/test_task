from datetime import datetime, timedelta, timezone

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.dao import TenderDAO
from src.db.enums import TenderStatus
from src.services.tender_service import TenderService
from src.tsk.tasks import check_expired_tenders


@pytest.mark.asyncio
async def test_close_expired_tenders_marks_as_lost(db_session: AsyncSession) -> None:
    """Истекший active тендер должен автоматически переводиться в lost."""
    tender = await TenderDAO.add(
        session=db_session,
        values={
            'title': 'Просроченный тендер',
            'status': TenderStatus.ACTIVE,
            'deadline': datetime.now(timezone.utc) - timedelta(hours=1),
        },
    )
    await db_session.commit()

    service = TenderService(db_session)
    updated = await service.close_expired_tenders()

    assert updated == 1
    await db_session.refresh(tender)
    assert tender.status == TenderStatus.LOST


@pytest.mark.asyncio
async def test_check_expired_tenders_persists_lost_status(db_session: AsyncSession) -> None:
    """Задача должна сохранять изменения status=lost в БД."""
    tender = await TenderDAO.add(
        session=db_session,
        values={
            'title': 'Просроченный тендер для задачи',
            'status': TenderStatus.ACTIVE,
            'deadline': datetime.now(timezone.utc) - timedelta(hours=1),
        },
    )
    await db_session.commit()

    updated = await check_expired_tenders()

    assert updated == 1

    db_session.expire_all()
    
    persisted_tender = await TenderDAO.find_one_or_none(
        session=db_session,
        filters={'title': 'Просроченный тендер для задачи'},
    )
    assert persisted_tender is not None
    assert persisted_tender.status == TenderStatus.LOST
    assert tender.id == persisted_tender.id


@pytest.mark.asyncio
async def test_create_tender(client: AsyncClient) -> None:
    """Тест создания тендера."""
    response = await client.post(
        '/api/v1/tenders',
        json={
            'title': 'Разработка CRM-системы',
            'description': 'Разработка CRM для отдела продаж',
            'customer': 'ООО Ромашка',
            'budget': 5000000,
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data['title'] == 'Разработка CRM-системы'
    assert data['status'] == 'draft'
    assert data['customer'] == 'ООО Ромашка'
    assert data['budget'] == 5000000
    assert 'id' in data


@pytest.mark.asyncio
async def test_get_tender(client: AsyncClient) -> None:
    """Тест получения тендера по ID."""
    create_resp = await client.post(
        '/api/v1/tenders',
        json={'title': 'Тестовый тендер'},
    )
    tender_id = create_resp.json()['id']

    response = await client.get(f'/api/v1/tenders/{tender_id}')
    assert response.status_code == 200
    assert response.json()['id'] == tender_id


@pytest.mark.asyncio
async def test_get_tender_not_found(client: AsyncClient) -> None:
    """Тест получения несуществующего тендера."""
    response = await client.get('/api/v1/tenders/99999')
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_tender(client: AsyncClient) -> None:
    """Тест обновления данных тендера."""
    create_resp = await client.post(
        '/api/v1/tenders',
        json={'title': 'Старое название', 'budget': 100},
    )
    tender_id = create_resp.json()['id']

    response = await client.patch(
        f'/api/v1/tenders/{tender_id}',
        json={'title': 'Новое название', 'budget': 200},
    )
    assert response.status_code == 200
    data = response.json()
    assert data['title'] == 'Новое название'
    assert data['budget'] == 200


@pytest.mark.asyncio
async def test_change_status_valid_transition(client: AsyncClient) -> None:
    """Тест валидного перехода статуса draft -> active."""
    create_resp = await client.post(
        '/api/v1/tenders',
        json={'title': 'Тендер для статуса'},
    )
    tender_id = create_resp.json()['id']

    response = await client.patch(
        f'/api/v1/tenders/{tender_id}/status',
        json={'status': 'active', 'changed_by': 'ivanov', 'reason': 'Опубликован'},
    )
    assert response.status_code == 200
    assert response.json()['status'] == 'active'


@pytest.mark.asyncio
async def test_change_status_invalid_transition(client: AsyncClient) -> None:
    """Тест невалидного перехода статуса draft -> won."""
    create_resp = await client.post(
        '/api/v1/tenders',
        json={'title': 'Тендер для невалидного перехода'},
    )
    tender_id = create_resp.json()['id']

    response = await client.patch(
        f'/api/v1/tenders/{tender_id}/status',
        json={'status': 'won', 'changed_by': 'ivanov'},
    )
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_change_status_invalid_value(client: AsyncClient) -> None:
    """Тест невалидного значения статуса."""
    create_resp = await client.post(
        '/api/v1/tenders',
        json={'title': 'Тендер для невалидного статуса'},
    )
    tender_id = create_resp.json()['id']

    response = await client.patch(
        f'/api/v1/tenders/{tender_id}/status',
        json={'status': 'invalid_status', 'changed_by': 'ivanov'},
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_status_history_logged(client: AsyncClient) -> None:
    """Тест логирования истории изменений статуса."""
    create_resp = await client.post(
        '/api/v1/tenders',
        json={'title': 'Тендер для истории'},
    )
    tender_id = create_resp.json()['id']

    # draft -> active
    await client.patch(
        f'/api/v1/tenders/{tender_id}/status',
        json={'status': 'active', 'changed_by': 'ivanov', 'reason': 'Опубликован'},
    )

    # active -> won
    await client.patch(
        f'/api/v1/tenders/{tender_id}/status',
        json={'status': 'won', 'changed_by': 'petrov', 'reason': 'Победа в тендере'},
    )

    response = await client.get(f'/api/v1/tenders/{tender_id}/history')
    assert response.status_code == 200
    data = response.json()
    assert data['total'] == 2
    assert data['items'][0]['to_status'] == 'won'
    assert data['items'][0]['from_status'] == 'active'
    assert data['items'][0]['changed_by'] == 'petrov'
    assert data['items'][1]['to_status'] == 'active'
    assert data['items'][1]['from_status'] == 'draft'
    assert data['items'][1]['changed_by'] == 'ivanov'


@pytest.mark.asyncio
async def test_list_tenders_pagination(client: AsyncClient) -> None:
    """Тест пагинации списка тендеров."""
    for i in range(3):
        await client.post(
            '/api/v1/tenders',
            json={'title': f'Тендер {i}'},
        )

    response = await client.get('/api/v1/tenders?page=1')
    assert response.status_code == 200
    data = response.json()
    assert data['page'] == 1
    assert data['total'] >= 3
    assert len(data['items']) > 0


@pytest.mark.asyncio
async def test_list_tenders_filter_by_status(client: AsyncClient) -> None:
    """Тест фильтрации тендеров по статусу."""
    create_resp = await client.post(
        '/api/v1/tenders',
        json={'title': 'Тендер для фильтра'},
    )
    tender_id = create_resp.json()['id']

    await client.patch(
        f'/api/v1/tenders/{tender_id}/status',
        json={'status': 'active', 'changed_by': 'ivanov'},
    )

    response = await client.get('/api/v1/tenders?status_filter=active')
    assert response.status_code == 200
    data = response.json()
    assert all(item['status'] == 'active' for item in data['items'])


@pytest.mark.asyncio
async def test_delete_tender(client: AsyncClient) -> None:
    """Тест удаления тендера."""
    create_resp = await client.post(
        '/api/v1/tenders',
        json={'title': 'Тендер для удаления'},
    )
    tender_id = create_resp.json()['id']

    response = await client.delete(f'/api/v1/tenders/{tender_id}')
    assert response.status_code == 204

    # Проверяем, что тендер удален
    get_resp = await client.get(f'/api/v1/tenders/{tender_id}')
    assert get_resp.status_code == 404