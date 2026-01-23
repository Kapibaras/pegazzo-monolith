"""add index on transaction.date

Revision ID: f53843902cce
Revises: 178f75115eae
Create Date: 2026-01-23 11:52:49.709801

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "f53843902cce"
down_revision: Union[str, Sequence[str], None] = "178f75115eae"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    """Upgrade schema."""
    op.create_index(
        "ix_transaction_date",
        "transaction",
        ["date"],
    )


def downgrade():
    """Downgrade schema."""
    op.drop_index(
        "ix_transaction_date",
        table_name="transaction",
    )
