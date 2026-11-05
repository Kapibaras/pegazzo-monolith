"""driver folio sequence and wider guarantor.relation

* ``driver_folio_seq`` backs the generated driver folio (``CD-{III}-{NNNN}``). It starts after the existing drivers.
* ``guarantor.relation`` goes from 10 to 50 characters (e.g. "Compañero de trabajo" did not fit).

Revision ID: f7a3c1d8e2b4
Revises: e5a1c7d9b3f2
Create Date: 2026-11-05 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'f7a3c1d8e2b4'
down_revision: Union[str, Sequence[str], None] = 'e5a1c7d9b3f2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create the folio sequence (continuing after existing drivers) and widen guarantor.relation."""
    op.execute('CREATE SEQUENCE IF NOT EXISTS driver_folio_seq START 1')
    op.execute(
        "SELECT setval('driver_folio_seq', GREATEST((SELECT COUNT(*) FROM driver), 1), (SELECT COUNT(*) > 0 FROM driver))"
    )
    op.alter_column('guarantor', 'relation', existing_type=sa.String(10), type_=sa.String(50), existing_nullable=False)


def downgrade() -> None:
    """Drop the sequence and narrow guarantor.relation (fails if a stored relation is longer than 10)."""
    op.alter_column('guarantor', 'relation', existing_type=sa.String(50), type_=sa.String(10), existing_nullable=False)
    op.execute('DROP SEQUENCE IF EXISTS driver_folio_seq')
