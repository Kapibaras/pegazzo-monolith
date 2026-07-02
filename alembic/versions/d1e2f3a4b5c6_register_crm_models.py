"""register CRM models and create base migrations

Revision ID: d1e2f3a4b5c6
Revises: bb39cb097284
Create Date: 2026-07-02 00:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "d1e2f3a4b5c6"
down_revision: Union[str, Sequence[str], None] = "bb39cb097284"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create all CRM tables and fix transaction.car_id."""
    # ------------------------------------------------------------------
    # Tables with no FK dependencies
    # ------------------------------------------------------------------
    op.create_table(
        "insurance",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=50), nullable=False),
        sa.Column("telephones", postgresql.ARRAY(sa.String()), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "associate",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=50), nullable=False),
        sa.Column("surnames", sa.String(length=100), nullable=False),
        sa.Column("telephones", postgresql.ARRAY(sa.String()), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "document",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("type", sa.String(length=20), nullable=False),
        sa.Column("url", sa.String(length=512), nullable=False),
        sa.Column("category", sa.String(length=50), nullable=False),
        sa.Column("confidence", sa.Numeric(5, 4), nullable=True),
        sa.Column("extracted_fields", sa.JSON(), nullable=True),
        sa.Column("expiry_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "reference",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=50), nullable=False),
        sa.Column("surnames", sa.String(length=100), nullable=False),
        sa.Column("telephones", postgresql.ARRAY(sa.String()), nullable=False),
        sa.Column("relation", sa.String(length=10), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "guarantor",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=50), nullable=False),
        sa.Column("surnames", sa.String(length=100), nullable=False),
        sa.Column("telephones", postgresql.ARRAY(sa.String()), nullable=False),
        sa.Column("address", sa.String(length=255), nullable=False),
        sa.Column("relation", sa.String(length=10), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "scheduler",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("category", sa.String(length=20), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("interval", sa.String(length=20), nullable=False),
        sa.Column("interval_count", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_launched_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )

    # ------------------------------------------------------------------
    # car — depends on insurance
    # ------------------------------------------------------------------
    op.create_table(
        "car",
        sa.Column("id", sa.String(length=15), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("make", sa.String(length=50), nullable=False),
        sa.Column("model", sa.String(length=50), nullable=False),
        sa.Column("year", sa.String(length=4), nullable=False),
        sa.Column("color", sa.String(length=30), nullable=False),
        sa.Column("body_type", sa.String(length=30), nullable=False),
        sa.Column("engine_type", sa.String(length=30), nullable=False),
        sa.Column("transmission", sa.String(length=20), nullable=False),
        sa.Column("vin", sa.String(length=17), nullable=False),
        sa.Column("engine_serial_number", sa.String(length=30), nullable=False),
        sa.Column("plate", sa.String(length=10), nullable=False),
        sa.Column("odometer", sa.Integer(), nullable=False),
        sa.Column("doors_number", sa.Integer(), nullable=False),
        sa.Column("passengers_number", sa.Integer(), nullable=False),
        sa.Column("unit_value", sa.Numeric(12, 2), nullable=False),
        sa.Column("unit_billing_value", sa.Numeric(12, 2), nullable=False),
        sa.Column("bill_number", sa.String(length=30), nullable=False),
        sa.Column("public_vehicle_registry", sa.String(length=30), nullable=False),
        sa.Column("alta_public_vehicle_registry", sa.DateTime(timezone=True), nullable=False),
        sa.Column("tire_specification", sa.String(length=20), nullable=False),
        sa.Column("features", sa.JSON(), nullable=False),
        sa.Column("details", sa.JSON(), nullable=False),
        sa.Column("legal_owner_name", sa.String(length=50), nullable=False),
        sa.Column("legal_owner_surnames", sa.String(length=100), nullable=False),
        sa.Column("battery_model", sa.String(length=20), nullable=False),
        sa.Column("battery_serial_number", sa.String(length=30), nullable=False),
        sa.Column("battery_date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("policy_number", sa.String(length=30), nullable=False),
        sa.Column("insurance_provider_id", sa.Integer(), nullable=False),
        sa.Column("policy_expiration_date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("policy_type", sa.String(length=20), nullable=False),
        sa.Column("financed_status", sa.String(length=20), nullable=False),
        sa.Column("agency_image", sa.String(length=512), nullable=True),
        sa.Column("photos", postgresql.ARRAY(sa.String(length=512)), nullable=True),
        sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["insurance_provider_id"], ["insurance.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("vin"),
        sa.UniqueConstraint("plate"),
    )

    # ------------------------------------------------------------------
    # driver — no FK deps (M2M tables come after)
    # ------------------------------------------------------------------
    op.create_table(
        "driver",
        sa.Column("id", sa.String(length=15), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("name", sa.String(length=50), nullable=False),
        sa.Column("surnames", sa.String(length=100), nullable=False),
        sa.Column("telephones", postgresql.ARRAY(sa.String(length=20)), nullable=False),
        sa.Column("license_number", sa.String(length=20), nullable=False),
        sa.Column("license_validity", sa.DateTime(timezone=True), nullable=False),
        sa.Column("identification_number", sa.String(length=20), nullable=False),
        sa.Column("address", sa.String(length=255), nullable=False),
        sa.Column("garage_address", postgresql.ARRAY(sa.String(length=255)), nullable=False),
        sa.Column("photo", sa.String(length=512), nullable=True),
        sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )

    # ------------------------------------------------------------------
    # M2M / junction tables — depend on their parent tables
    # ------------------------------------------------------------------
    op.create_table(
        "associate_car",
        sa.Column("associate_id", sa.Integer(), nullable=False),
        sa.Column("car_id", sa.String(length=15), nullable=False),
        sa.ForeignKeyConstraint(["associate_id"], ["associate.id"]),
        sa.ForeignKeyConstraint(["car_id"], ["car.id"]),
        sa.PrimaryKeyConstraint("associate_id", "car_id"),
    )

    op.create_table(
        "car_document",
        sa.Column("car_id", sa.String(length=15), nullable=False),
        sa.Column("document_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["car_id"], ["car.id"]),
        sa.ForeignKeyConstraint(["document_id"], ["document.id"]),
        sa.PrimaryKeyConstraint("car_id", "document_id"),
    )

    op.create_table(
        "guarantor_document",
        sa.Column("guarantor_id", sa.Integer(), nullable=False),
        sa.Column("document_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["guarantor_id"], ["guarantor.id"]),
        sa.ForeignKeyConstraint(["document_id"], ["document.id"]),
        sa.PrimaryKeyConstraint("guarantor_id", "document_id"),
    )

    op.create_table(
        "reference_document",
        sa.Column("reference_id", sa.Integer(), nullable=False),
        sa.Column("document_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["reference_id"], ["reference.id"]),
        sa.ForeignKeyConstraint(["document_id"], ["document.id"]),
        sa.PrimaryKeyConstraint("reference_id", "document_id"),
    )

    op.create_table(
        "driver_document",
        sa.Column("driver_id", sa.String(length=15), nullable=False),
        sa.Column("document_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["driver_id"], ["driver.id"]),
        sa.ForeignKeyConstraint(["document_id"], ["document.id"]),
        sa.PrimaryKeyConstraint("driver_id", "document_id"),
    )

    op.create_table(
        "driver_reference",
        sa.Column("driver_id", sa.String(length=15), nullable=False),
        sa.Column("reference_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["driver_id"], ["driver.id"]),
        sa.ForeignKeyConstraint(["reference_id"], ["reference.id"]),
        sa.PrimaryKeyConstraint("driver_id", "reference_id"),
    )

    op.create_table(
        "driver_guarantor",
        sa.Column("driver_id", sa.String(length=15), nullable=False),
        sa.Column("guarantor_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["driver_id"], ["driver.id"]),
        sa.ForeignKeyConstraint(["guarantor_id"], ["guarantor.id"]),
        sa.PrimaryKeyConstraint("driver_id", "guarantor_id"),
    )

    # ------------------------------------------------------------------
    # contract and incidence — depend on car + driver
    # ------------------------------------------------------------------
    op.create_table(
        "contract",
        sa.Column("id", sa.String(length=15), nullable=False),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("end_date", sa.Date(), nullable=False),
        sa.Column("type", sa.String(length=10), nullable=False),
        sa.Column("amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("guarantee_amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("sanction_amount", sa.Numeric(12, 2), nullable=True),
        sa.Column("due_amount", sa.Numeric(12, 2), nullable=True),
        sa.Column("signed_document_in", sa.String(length=512), nullable=True),
        sa.Column("signed_document_out", sa.String(length=512), nullable=True),
        sa.Column("signed_checklist_in", sa.String(length=512), nullable=True),
        sa.Column("signed_checklist_out", sa.String(length=512), nullable=True),
        sa.Column("car_id", sa.String(length=15), nullable=True),
        sa.Column("driver_id", sa.String(length=15), nullable=True),
        sa.ForeignKeyConstraint(["car_id"], ["car.id"]),
        sa.ForeignKeyConstraint(["driver_id"], ["driver.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "incidence",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("type", sa.String(length=50), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("location", sa.String(length=255), nullable=True),
        sa.Column("odometer", sa.Integer(), nullable=True),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("car_id", sa.String(length=15), nullable=True),
        sa.Column("driver_id", sa.String(length=15), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["car_id"], ["car.id"]),
        sa.ForeignKeyConstraint(["driver_id"], ["driver.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "incidence_document",
        sa.Column("incidence_id", sa.Integer(), nullable=False),
        sa.Column("document_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["incidence_id"], ["incidence.id"]),
        sa.ForeignKeyConstraint(["document_id"], ["document.id"]),
        sa.PrimaryKeyConstraint("incidence_id", "document_id"),
    )

    op.create_table(
        "event",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("category", sa.String(length=20), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("car_id", sa.String(length=15), nullable=True),
        sa.Column("driver_id", sa.String(length=15), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("to_resolve_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("accepted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["car_id"], ["car.id"]),
        sa.ForeignKeyConstraint(["driver_id"], ["driver.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "event_document",
        sa.Column("event_id", sa.Integer(), nullable=False),
        sa.Column("document_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["event_id"], ["event.id"]),
        sa.ForeignKeyConstraint(["document_id"], ["document.id"]),
        sa.PrimaryKeyConstraint("event_id", "document_id"),
    )

    # ------------------------------------------------------------------
    # Alter existing transaction.car_id: Integer → String(15) FK
    # ------------------------------------------------------------------
    op.alter_column(
        "transaction",
        "car_id",
        existing_type=sa.Integer(),
        type_=sa.String(length=15),
        existing_nullable=True,
        postgresql_using="car_id::text",
    )
    op.create_foreign_key(
        "fk_transaction_car_id",
        "transaction",
        "car",
        ["car_id"],
        ["id"],
    )


def downgrade() -> None:
    """Drop all CRM tables and revert transaction.car_id."""
    # Revert transaction.car_id first (FK references car which we're dropping)
    op.drop_constraint("fk_transaction_car_id", "transaction", type_="foreignkey")
    op.alter_column(
        "transaction",
        "car_id",
        existing_type=sa.String(length=15),
        type_=sa.Integer(),
        existing_nullable=True,
        postgresql_using="car_id::integer",
    )

    # Drop in reverse dependency order
    op.drop_table("event_document")
    op.drop_table("event")
    op.drop_table("incidence_document")
    op.drop_table("incidence")
    op.drop_table("contract")
    op.drop_table("driver_guarantor")
    op.drop_table("driver_reference")
    op.drop_table("driver_document")
    op.drop_table("reference_document")
    op.drop_table("guarantor_document")
    op.drop_table("car_document")
    op.drop_table("associate_car")
    op.drop_table("driver")
    op.drop_table("car")
    op.drop_table("scheduler")
    op.drop_table("guarantor")
    op.drop_table("reference")
    op.drop_table("document")
    op.drop_table("associate")
    op.drop_table("insurance")
