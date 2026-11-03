"""add deleted_at to driver (PGZ-142)

Revision ID: b7d2e9f4c1a6
Revises: 1ecf6523511c
Create Date: 2026-11-02 18:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'b7d2e9f4c1a6'
down_revision: Union[str, Sequence[str], None] = '1ecf6523511c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add the soft-delete marker used when a driver with history is deleted."""
    op.add_column('driver', sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    """Remove the soft-delete marker."""
    op.drop_column('driver', 'deleted_at')
