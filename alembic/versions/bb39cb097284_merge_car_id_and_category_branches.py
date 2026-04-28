"""merge car_id and category branches

Revision ID: bb39cb097284
Revises: b7c9e2f4a8d1, c4d1f7e3b9a2
Create Date: 2026-04-28 15:58:13.241754

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'bb39cb097284'
down_revision: Union[str, Sequence[str], None] = ('b7c9e2f4a8d1', 'c4d1f7e3b9a2')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
