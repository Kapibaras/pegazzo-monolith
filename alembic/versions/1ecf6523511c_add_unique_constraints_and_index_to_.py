"""add unique constraints and index to driver

Revision ID: 1ecf6523511c
Revises: 7191b37efe63
Create Date: 2026-11-01 13:05:02.098137

"""
from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = '1ecf6523511c'
down_revision: Union[str, Sequence[str], None] = '7191b37efe63'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_index(op.f('ix_driver_license_number'), 'driver', ['license_number'], unique=True)
    op.create_unique_constraint('uq_driver_identification_number', 'driver', ['identification_number'])


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint('uq_driver_identification_number', 'driver', type_='unique')
    op.drop_index(op.f('ix_driver_license_number'), table_name='driver')
