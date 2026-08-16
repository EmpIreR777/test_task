from enum import StrEnum


class TenderStatus(StrEnum):
    """Статус тендера."""

    DRAFT = 'draft'
    ACTIVE = 'active'
    WON = 'won'
    LOST = 'lost'


class TenderStatusTransition(StrEnum):
    """Допустимые переходы статусов тендера."""

    DRAFT_TO_ACTIVE = 'draft -> active'
    ACTIVE_TO_WON = 'active -> won'
    ACTIVE_TO_LOST = 'active -> lost'
    DRAFT_TO_LOST = 'draft -> lost'
