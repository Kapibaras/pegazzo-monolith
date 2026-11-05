"""driver.license_validity nullable (permanent licenses)

Some licenses never expire. ``NULL`` now means a permanent license.

Revision ID: b9d5f2a7c3e1
Revises: a8c4e1f6b2d9
Create Date: 2026-11-05 18:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'b9d5f2a7c3e1'
down_revision: Union[str, Sequence[str], None] = 'a8c4e1f6b2d9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Allow a driver without license expiry date."""
    op.alter_column('driver', 'license_validity', existing_type=sa.DateTime(timezone=True), nullable=True)


def downgrade() -> None:
    """Permanent licenses get a far-future date so the column can be NOT NULL again."""
    op.execute("UPDATE driver SET license_validity = '2999-12-31T00:00:00+00' WHERE license_validity IS NULL")
    op.alter_column('driver', 'license_validity', existing_type=sa.DateTime(timezone=True), nullable=False)
