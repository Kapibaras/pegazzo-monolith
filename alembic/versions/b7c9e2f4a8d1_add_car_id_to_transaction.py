"""add car_id to transaction table

Revision ID: b7c9e2f4a8d1
Revises: a1b2c3d4e5f6
Create Date: 2026-04-19 00:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "b7c9e2f4a8d1"
down_revision: Union[str, Sequence[str], None] = "a1b2c3d4e5f6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add nullable car_id column to transaction table."""
    op.add_column(
        "transaction",
        sa.Column("car_id", sa.Integer(), nullable=True),
    )


def downgrade() -> None:
    """Remove car_id column from transaction table."""
    op.drop_column("transaction", "car_id")
