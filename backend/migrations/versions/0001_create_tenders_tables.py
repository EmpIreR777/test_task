"""create tenders tables

Revision ID: 0001
Revises:
Create Date: 2026-08-15
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = '0001'
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Создаёт таблицы tenders и tender_status_history."""
    op.execute('CREATE SCHEMA IF NOT EXISTS tenders')
    op.execute('CREATE EXTENSION IF NOT EXISTS pg_trgm')

    op.create_table(
        'tenders',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('customer', sa.String(length=255), nullable=True),
        sa.Column('budget', sa.Integer(), nullable=True),
        sa.Column('deadline', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        schema='tenders',
    )
    op.create_index('ix_tenders_status_created_at', 'tenders', ['status', 'created_at'], schema='tenders')
    op.create_index(
        'ix_tenders_title_trgm',
        'tenders',
        ['title'],
        unique=False,
        postgresql_using='gin',
        postgresql_ops={'title': 'gin_trgm_ops'},
        schema='tenders',
    )

    op.create_table(
        'tender_status_history',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('tender_id', sa.Integer(), nullable=False),
        sa.Column('from_status', sa.String(length=50), nullable=True),
        sa.Column('to_status', sa.String(length=50), nullable=False),
        sa.Column('changed_by', sa.String(length=255), nullable=False),
        sa.Column('reason', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['tender_id'], ['tenders.tenders.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        schema='tenders',
    )
    op.create_index(
        'ix_tender_status_history_tender_id_created_at',
        'tender_status_history',
        ['tender_id', 'created_at'],
        schema='tenders',
    )
    op.create_index(
        'ix_tender_status_history_tender_id',
        'tender_status_history',
        ['tender_id'],
        unique=False,
        schema='tenders',
    )


def downgrade() -> None:
    """Удаляет таблицы tenders и tender_status_history."""
    op.drop_index('ix_tender_status_history_tender_id', table_name='tender_status_history', schema='tenders')
    op.drop_index(
        'ix_tender_status_history_tender_id_created_at',
        table_name='tender_status_history',
        schema='tenders',
    )
    op.drop_table('tender_status_history', schema='tenders')

    op.drop_index('ix_tenders_title_trgm', table_name='tenders', schema='tenders')
    op.drop_index('ix_tenders_status_created_at', table_name='tenders', schema='tenders')
    op.drop_table('tenders', schema='tenders')
