"""add deleted_at to car (PGZ-130)

Revision ID: a4b8c1d2e3f5
Revises: 7191b37efe63
Create Date: 2026-10-27 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'a4b8c1d2e3f5'
down_revision: Union[str, Sequence[str], None] = '7191b37efe63'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add the soft-delete marker used when a car with history is deleted."""
    op.add_column('car', sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    """Remove the soft-delete marker."""
    op.drop_column('car', 'deleted_at')
