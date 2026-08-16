from fastapi import APIRouter

from src.core.config import settings

from .tenders_router import router as tenders_router

router = APIRouter(prefix=settings.API_PREFIX)
router.include_router(tenders_router)

__all__ = ['router']
