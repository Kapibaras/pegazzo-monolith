"""driver garages as an entity, structured addresses

* ``address_fields`` (JSON) on driver and guarantor keeps the address split into fields; ``address`` stays as the
  joined text (legacy rows have no fields, only the text).
* ``driver_garage`` / ``garage_document`` replace ``driver.garage_address`` so every garage has its own documents.
  Existing garage texts are migrated as garages without structured fields.

Revision ID: a8c4e1f6b2d9
Revises: f7a3c1d8e2b4
Create Date: 2026-11-05 14:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "a8c4e1f6b2d9"
down_revision: Union[str, Sequence[str], None] = "f7a3c1d8e2b4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add the structured fields, create the garage tables and move the garage texts."""
    op.add_column("driver", sa.Column("address_fields", sa.JSON(), nullable=True))
    op.add_column("guarantor", sa.Column("address_fields", sa.JSON(), nullable=True))

    op.create_table(
        "driver_garage",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("driver_id", sa.String(15), sa.ForeignKey("driver.id"), nullable=False),
        sa.Column("address", sa.String(255), nullable=False),
        sa.Column("address_fields", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_driver_garage_driver_id", "driver_garage", ["driver_id"])
    op.create_table(
        "garage_document",
        sa.Column("garage_id", sa.Integer(), sa.ForeignKey("driver_garage.id"), primary_key=True, nullable=False),
        sa.Column("document_id", sa.Integer(), sa.ForeignKey("document.id"), primary_key=True, nullable=False),
    )

    op.execute(
        "INSERT INTO driver_garage (driver_id, address) "
        "SELECT id, unnest(garage_address) FROM driver WHERE garage_address IS NOT NULL"
    )
    op.drop_column("driver", "garage_address")


def downgrade() -> None:
    """Bring ``garage_address`` back from the garages (their documents and structured fields are lost)."""
    op.add_column("driver", sa.Column("garage_address", sa.ARRAY(sa.String(255)), nullable=True))
    op.execute(
        "UPDATE driver SET garage_address = COALESCE("
        "(SELECT array_agg(g.address ORDER BY g.id) FROM driver_garage g WHERE g.driver_id = driver.id), '{}')"
    )
    op.alter_column("driver", "garage_address", nullable=False)

    op.drop_table("garage_document")
    op.drop_index("ix_driver_garage_driver_id", table_name="driver_garage")
    op.drop_table("driver_garage")
    op.drop_column("guarantor", "address_fields")
    op.drop_column("driver", "address_fields")
