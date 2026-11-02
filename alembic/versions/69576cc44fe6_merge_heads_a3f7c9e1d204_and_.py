"""merge heads a3f7c9e1d204 and a4b8c1d2e3f5

Revision ID: 69576cc44fe6
Revises: a3f7c9e1d204, a4b8c1d2e3f5
Create Date: 2026-11-02 15:01:32.380556

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '69576cc44fe6'
down_revision: Union[str, Sequence[str], None] = ('a3f7c9e1d204', 'a4b8c1d2e3f5')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
