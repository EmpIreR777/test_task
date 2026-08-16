from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class TenderCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    customer: str | None = Field(default=None, max_length=255)
    budget: int | None = Field(default=None, ge=0)
    deadline: datetime | None = None


class TenderUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    customer: str | None = Field(default=None, max_length=255)
    budget: int | None = Field(default=None, ge=0)
    deadline: datetime | None = None


class TenderStatusUpdate(BaseModel):
    status: str
    changed_by: str = Field(..., min_length=1, max_length=255)
    reason: str | None = None


class TenderItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    description: str | None
    status: str
    customer: str | None
    budget: int | None
    deadline: datetime | None
    created_at: datetime
    updated_at: datetime


class TenderStatusHistoryItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    tender_id: int
    from_status: str | None
    to_status: str
    changed_by: str
    reason: str | None
    created_at: datetime


class PaginatedTenderResponse(BaseModel):
    items: list[TenderItem]
    page: int
    page_size: int
    total: int
    total_pages: int


class PaginatedHistoryResponse(BaseModel):
    items: list[TenderStatusHistoryItem]
    page: int
    page_size: int
    total: int
    total_pages: int
