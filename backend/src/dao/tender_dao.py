from src.dao.base_dao import BaseDAO
from src.db.models import Tender, TenderStatusHistory


class TenderDAO(BaseDAO[Tender]):
    model = Tender


class TenderStatusHistoryDAO(BaseDAO[TenderStatusHistory]):
    model = TenderStatusHistory
