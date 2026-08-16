from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, Text, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from src.db.enums import TenderStatus


class Base(DeclarativeBase):
    """Базовый класс модели с общими полями."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
    )

    __abstract__ = True


class Tender(Base):
    __tablename__ = 'tenders'
    __table_args__ = (
        Index('ix_tenders_status_created_at', 'status', 'created_at'),
        Index('ix_tenders_title_trgm', 'title', postgresql_using='gin', postgresql_ops={'title': 'gin_trgm_ops'}),
        {'schema': 'tenders'},
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default=TenderStatus.DRAFT)
    customer: Mapped[str | None] = mapped_column(String(255), nullable=True)
    budget: Mapped[int | None] = mapped_column(Integer, nullable=True)
    deadline: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class TenderStatusHistory(Base):
    __tablename__ = 'tender_status_history'
    __table_args__ = (
        Index('ix_tender_status_history_tender_id_created_at', 'tender_id', 'created_at'),
        {'schema': 'tenders'},
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    tender_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey('tenders.tenders.id', ondelete='CASCADE'),
        nullable=False,
        index=True,
    )
    from_status: Mapped[str | None] = mapped_column(String(50), nullable=True)
    to_status: Mapped[str] = mapped_column(String(50), nullable=False)
    changed_by: Mapped[str] = mapped_column(String(255), nullable=False)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
