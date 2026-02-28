"""alter transaction.date to timestamptz

Revision ID: 3c8e2f1a9d47
Revises: f53843902cce
Create Date: 2026-02-28 00:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "3c8e2f1a9d47"
down_revision: Union[str, Sequence[str], None] = "f53843902cce"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Convert transaction.date from timestamp to timestamptz (UTC)."""
    op.alter_column(
        "transaction",
        "date",
        type_=sa.DateTime(timezone=True),
        existing_type=sa.DateTime(timezone=False),
        existing_nullable=False,
        postgresql_using="date AT TIME ZONE 'UTC'",
    )


def downgrade() -> None:
    """Revert transaction.date from timestamptz to timestamp."""
    op.alter_column(
        "transaction",
        "date",
        type_=sa.DateTime(timezone=False),
        existing_type=sa.DateTime(timezone=True),
        existing_nullable=False,
        postgresql_using="date AT TIME ZONE 'UTC'",
    )
