"""Add car_model and us_associate tables - PGZ-150

Revision ID: 3066a4ec1894
Revises: d1e2f3a4b5c6
Create Date: 2026-08-12 16:50:52.929411

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = '3066a4ec1894'
down_revision: Union[str, Sequence[str], None] = 'd1e2f3a4b5c6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'car_model',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('make', sa.String(length=50), nullable=False),
        sa.Column('model', sa.String(length=50), nullable=False),
        sa.Column('abbreviation', sa.String(length=10), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('make', 'model', name='uq_car_model_make_model'),
    )
    op.create_table(
        'owner_associate',
        sa.Column('associate_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['associate_id'], ['associate.id']),
        sa.PrimaryKeyConstraint('associate_id'),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('owner_associate')
    op.drop_table('car_model')
