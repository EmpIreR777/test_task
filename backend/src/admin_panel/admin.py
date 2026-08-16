from fastapi import FastAPI
from sqladmin import Admin, ModelView
from sqlalchemy.ext.asyncio import AsyncEngine

from src.db.models import Tender, TenderStatusHistory


class TenderAdmin(ModelView, model=Tender):
    """Интерфейс управления тендерами в админ панели."""

    name = 'Тендер'
    name_plural = 'Тендеры'
    icon = 'fa-solid fa-folder'

    column_list = [
        Tender.id,
        Tender.title,
        Tender.status,
        Tender.customer,
        Tender.budget,
        Tender.created_at,
    ]

    column_searchable_list = [
        Tender.id,
        Tender.title,
        Tender.customer,
    ]

    column_sortable_list = [
        Tender.created_at,
        Tender.status,
        Tender.budget,
    ]


class TenderStatusHistoryAdmin(ModelView, model=TenderStatusHistory):
    """Интерфейс истории статусов тендеров."""

    name = 'Статус тендера'
    name_plural = 'Статусы тендеров'
    icon = 'fa-solid fa-history'

    column_list = [
        TenderStatusHistory.id,
        TenderStatusHistory.tender_id,
        TenderStatusHistory.from_status,
        TenderStatusHistory.to_status,
        TenderStatusHistory.changed_by,
        TenderStatusHistory.created_at,
    ]

    column_searchable_list = [
        TenderStatusHistory.tender_id,
        TenderStatusHistory.changed_by,
    ]

    column_sortable_list = [
        TenderStatusHistory.created_at,
        TenderStatusHistory.to_status,
    ]


def register_admin(app: FastAPI, engine: AsyncEngine) -> Admin:
    """Подключает админ-панель sqladmin к приложению."""
    admin = Admin(app=app, engine=engine, title='Админ Панель')
    admin.add_view(TenderAdmin)
    admin.add_view(TenderStatusHistoryAdmin)
    return admin
