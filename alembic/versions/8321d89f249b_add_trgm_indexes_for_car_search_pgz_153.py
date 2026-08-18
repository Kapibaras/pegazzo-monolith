"""Add pg_trgm extension and GIN indexes for car fuzzy search - PGZ-153

Revision ID: 8321d89f249b
Revises: 10536474dfd8
Create Date: 2026-08-18 00:00:00.000000

"""

from typing import Sequence, Union

from alembic import op

revision: str = "8321d89f249b"
down_revision: Union[str, None] = "10536474dfd8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")
    op.execute("CREATE INDEX IF NOT EXISTS ix_car_make_trgm ON car USING gin (make gin_trgm_ops)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_car_model_trgm ON car USING gin (model gin_trgm_ops)")


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_car_model_trgm")
    op.execute("DROP INDEX IF EXISTS ix_car_make_trgm")
