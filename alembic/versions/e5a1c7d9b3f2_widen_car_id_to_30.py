"""widen car.id (internal folio) from 15 to 30 characters

The computed folio (e.g. ``US-GF-MZ2(TA)-01``) is 16+ characters, so it never fit in ``String(15)``.

Revision ID: e5a1c7d9b3f2
Revises: b7d2e9f4c1a6
Create Date: 2026-11-04 01:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'e5a1c7d9b3f2'
down_revision: Union[str, Sequence[str], None] = 'b7d2e9f4c1a6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# (table, column, nullable) for every column that stores a car id.
_CAR_ID_COLUMNS = [
    ('car_document', 'car_id', False),
    ('associate_car', 'car_id', False),
    ('transaction', 'car_id', True),
    ('contract', 'car_id', True),
    ('event', 'car_id', True),
    ('incidence', 'car_id', True),
]


def _alter(from_length: int, to_length: int) -> None:
    op.alter_column(
        'car', 'id', existing_type=sa.String(from_length), type_=sa.String(to_length), existing_nullable=False
    )
    for table, column, nullable in _CAR_ID_COLUMNS:
        op.alter_column(
            table, column, existing_type=sa.String(from_length), type_=sa.String(to_length), existing_nullable=nullable
        )


def upgrade() -> None:
    """Widen car.id and every column that references it."""
    _alter(15, 30)


def downgrade() -> None:
    """Narrow back to 15 characters (fails if any stored car id is longer)."""
    _alter(30, 15)
