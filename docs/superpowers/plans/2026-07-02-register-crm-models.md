# [MTH] Register CRM Models & Base Migrations Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix CRM model inconsistencies, add required new fields, register all models in Alembic's scope, and author the migration that creates every CRM table.

**Architecture:** Model-only changes — no routers, services, or repositories. All CRM models already exist as Python files but are unregistered. This plan fixes their inconsistencies, adds new fields, registers them in `app/models/__init__.py`, and writes a hand-authored Alembic migration chained off the current head (`bb39cb097284`).

**Tech Stack:** SQLAlchemy 2.x ORM, Alembic, PostgreSQL (ARRAY, JSON, TIMESTAMPTZ), Python StrEnum, pipenv

## Global Constraints

- No endpoints, routers, services, or repositories touched
- All `DateTime` columns must use `DateTime(timezone=True)` → maps to `TIMESTAMPTZ` in Postgres
- Status String columns must be `String(20)` minimum (`IN_MAINTENANCE` is 14 chars, `SUSPENDED` is 9)
- Canonical table name for references entity: `"reference"` (singular)
- `Associate.id` is `Integer`; `associate_car.associate_id` must also be `Integer` (FK type match)
- Migration `down_revision` must point to `bb39cb097284`
- `alembic upgrade head` and `alembic downgrade -1` must both succeed on a clean database

---

## File Map

| File | Action | Responsibility |
|------|--------|----------------|
| `app/enum/crm.py` | **Create** | `CarStatus` and `DriverStatus` StrEnums |
| `app/models/driver.py` | **Modify** | Fix Reference tablename + FK, widen status, add `archived_at` + `photo`, rename M2M table |
| `app/models/car.py` | **Modify** | Fix associate_id type, widen status, remove owner columns, add `archived_at` + image fields |
| `app/models/document.py` | **Modify** | Add `category`, `confidence`, `extracted_fields`, `expiry_date` |
| `app/models/contract.py` | **Modify** | Fix `gurantee_amount` → `guarantee_amount` |
| `app/models/balance.py` | **Modify** | Change `transaction.car_id` from bare `Integer` to `String(15)` FK |
| `app/models/__init__.py` | **Modify** | Export all CRM model classes and association tables |
| `alembic/versions/d1e2f3a4b5c6_register_crm_models.py` | **Create** | Migration: CREATE all CRM tables + ALTER transaction.car_id |

---

### Task 1: Add CRM status enums

**Files:**
- Create: `app/enum/crm.py`
- Modify: `app/enum/__init__.py`

**Interfaces:**
- Produces: `CarStatus`, `DriverStatus` StrEnums — used for documentation only (columns stay as `String`)

- [ ] **Step 1: Create `app/enum/crm.py`**

```python
from enum import StrEnum


class CarStatus(StrEnum):
    """Enum for car operational status."""

    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    IN_MAINTENANCE = "IN_MAINTENANCE"


class DriverStatus(StrEnum):
    """Enum for driver operational status."""

    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    SUSPENDED = "SUSPENDED"
```

- [ ] **Step 2: Check `app/enum/__init__.py` and add exports if it has them**

Open `app/enum/__init__.py`. If it explicitly exports names, add:

```python
from .crm import CarStatus, DriverStatus
```

- [ ] **Step 3: Verify import works**

```bash
python -c "from app.enum.crm import CarStatus, DriverStatus; print(CarStatus.IN_MAINTENANCE, DriverStatus.SUSPENDED)"
```

Expected output: `IN_MAINTENANCE SUSPENDED`

- [ ] **Step 4: Commit**

```bash
git add app/enum/crm.py app/enum/__init__.py
git commit -m "feat: add CarStatus and DriverStatus enums for CRM models"
```

---

### Task 2: Fix `app/models/driver.py`

**Files:**
- Modify: `app/models/driver.py`

**What to change:**
1. Rename `references_document_table` → `reference_document_table`; FK `"references.id"` → `"reference.id"`
2. `Reference.__tablename__` → `"reference"` (was `"references"`)
3. `Driver.status` → `String(20)` (was `String(10)`)
4. Add `Driver.archived_at = Column(DateTime(timezone=True), nullable=True)`
5. Add `Driver.photo = Column(String(512), nullable=True)`

- [ ] **Step 1: Rewrite `app/models/driver.py` with all fixes**

```python
from sqlalchemy import Column, ForeignKey, Integer, String, Table
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.types import DateTime

from app.database.base import Base

driver_document_table = Table(
    "driver_document",
    Base.metadata,
    Column("driver_id", String(15), ForeignKey("driver.id"), primary_key=True, nullable=False),
    Column("document_id", Integer, ForeignKey("document.id"), primary_key=True, nullable=False),
)

driver_guarantor_table = Table(
    "driver_guarantor",
    Base.metadata,
    Column("driver_id", String(15), ForeignKey("driver.id"), primary_key=True, nullable=False),
    Column("guarantor_id", Integer, ForeignKey("guarantor.id"), primary_key=True, nullable=False),
)

guarantor_document_table = Table(
    "guarantor_document",
    Base.metadata,
    Column("guarantor_id", Integer, ForeignKey("guarantor.id"), primary_key=True, nullable=False),
    Column("document_id", Integer, ForeignKey("document.id"), primary_key=True, nullable=False),
)

reference_document_table = Table(
    "reference_document",
    Base.metadata,
    Column("reference_id", Integer, ForeignKey("reference.id"), primary_key=True, nullable=False),
    Column("document_id", Integer, ForeignKey("document.id"), primary_key=True, nullable=False),
)

driver_reference_table = Table(
    "driver_reference",
    Base.metadata,
    Column("driver_id", String(15), ForeignKey("driver.id"), primary_key=True, nullable=False),
    Column("reference_id", Integer, ForeignKey("reference.id"), primary_key=True, nullable=False),
)


class Driver(Base):
    """Driver model class."""

    __tablename__ = "driver"
    id = Column(String(15), primary_key=True, nullable=False)
    status = Column(String(20), nullable=False)
    name = Column(String(50), nullable=False)
    surnames = Column(String(100), nullable=False)
    telephones = Column(ARRAY(String(20)), nullable=False)
    license_number = Column(String(20), nullable=False)
    license_validity = Column(DateTime(timezone=True), default=func.now(), nullable=False)
    identification_number = Column(String(20), nullable=False)
    address = Column(String(255), nullable=False)
    references = relationship("Reference", secondary=driver_reference_table)
    documents = relationship("Document", secondary=driver_document_table)
    guarantors = relationship("Guarantor", secondary=driver_guarantor_table)
    garage_address = Column(ARRAY(String(255)), nullable=False)
    photo = Column(String(512), nullable=True)
    archived_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=func.now(), onupdate=func.now(), nullable=False)


class Reference(Base):
    """Reference model class."""

    __tablename__ = "reference"
    id = Column(Integer, primary_key=True, nullable=False)
    name = Column(String(50), nullable=False)
    surnames = Column(String(100), nullable=False)
    telephones = Column(ARRAY(String), nullable=False)
    relation = Column(String(10), nullable=False)
    created_at = Column(DateTime(timezone=True), default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=func.now(), onupdate=func.now(), nullable=False)


class Guarantor(Base):
    """Guarantor model class."""

    __tablename__ = "guarantor"
    id = Column(Integer, primary_key=True, nullable=False)
    name = Column(String(50), nullable=False)
    surnames = Column(String(100), nullable=False)
    telephones = Column(ARRAY(String), nullable=False)
    address = Column(String(255), nullable=False)
    relation = Column(String(10), nullable=False)
    documents = relationship("Document", secondary=guarantor_document_table)
    created_at = Column(DateTime(timezone=True), default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=func.now(), onupdate=func.now(), nullable=False)
```

- [ ] **Step 2: Verify import**

```bash
python -c "from app.models.driver import Driver, Reference, Guarantor; print('OK')"
```

Expected: `OK`

- [ ] **Step 3: Commit**

```bash
git add app/models/driver.py
git commit -m "fix: canonicalize reference table name, widen status, add photo and archived_at to Driver"
```

---

### Task 3: Fix `app/models/car.py`

**Files:**
- Modify: `app/models/car.py`

**What to change:**
1. `associate_car.associate_id` → `Integer` (was `String(15)`) to match `Associate.id`
2. `Car.status` → `String(20)` (was `String(10)`)
3. Remove `Car.owner_name` and `Car.owner_surnames`
4. Add `Car.archived_at = Column(DateTime(timezone=True), nullable=True)`
5. Add `Car.agency_image = Column(String(512), nullable=True)`
6. Add `Car.photos = Column(ARRAY(String(512)), nullable=True)`

- [ ] **Step 1: Rewrite `app/models/car.py` with all fixes**

```python
from sqlalchemy import JSON, Column, ForeignKey, Integer, Numeric, String, Table
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.types import DateTime

from app.database.base import Base

car_document_table = Table(
    "car_document",
    Base.metadata,
    Column("car_id", String(15), ForeignKey("car.id"), primary_key=True, nullable=False),
    Column("document_id", Integer, ForeignKey("document.id"), primary_key=True, nullable=False),
)

associate_car = Table(
    "associate_car",
    Base.metadata,
    Column("associate_id", Integer, ForeignKey("associate.id"), primary_key=True, nullable=False),
    Column("car_id", String(15), ForeignKey("car.id"), primary_key=True, nullable=False),
)


class Car(Base):
    """Car model class."""

    __tablename__ = "car"
    id = Column(String(15), primary_key=True, nullable=False)
    status = Column(String(20), nullable=False)
    make = Column(String(50), nullable=False)
    model = Column(String(50), nullable=False)
    year = Column(String(4), nullable=False)
    color = Column(String(30), nullable=False)
    body_type = Column(String(30), nullable=False)
    engine_type = Column(String(30), nullable=False)
    transmission = Column(String(20), nullable=False)
    vin = Column(String(17), nullable=False, unique=True)
    engine_serial_number = Column(String(30), nullable=False)
    plate = Column(String(10), nullable=False, unique=True)
    odometer = Column(Integer, nullable=False)
    doors_number = Column(Integer, nullable=False)
    passengers_number = Column(Integer, nullable=False)
    unit_value = Column(Numeric(12, 2), nullable=False)
    unit_billing_value = Column(Numeric(12, 2), nullable=False)
    bill_number = Column(String(30), nullable=False)
    public_vehicle_registry = Column(String(30), nullable=False)
    alta_public_vehicle_registry = Column(DateTime(timezone=True), default=func.now(), nullable=False)
    tire_specification = Column(String(20), nullable=False)
    features = Column(JSON, nullable=False)
    details = Column(JSON, nullable=False)
    legal_owner_name = Column(String(50), nullable=False)
    legal_owner_surnames = Column(String(100), nullable=False)
    associate = relationship("Associate", secondary=associate_car, back_populates="cars")
    battery_model = Column(String(20), nullable=False)
    battery_serial_number = Column(String(30), nullable=False)
    battery_date = Column(DateTime(timezone=True), default=func.now(), nullable=False)
    policy_number = Column(String(30), nullable=False)
    insurance_provider_id = Column(Integer, ForeignKey("insurance.id"), nullable=False)
    insurance_provider = relationship("Insurance")
    policy_expiration_date = Column(DateTime(timezone=True), default=func.now(), nullable=False)
    policy_type = Column(String(20), nullable=False)
    financed_status = Column(String(20), nullable=False)
    agency_image = Column(String(512), nullable=True)
    photos = Column(ARRAY(String(512)), nullable=True)
    archived_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=func.now(), onupdate=func.now(), nullable=False)


class Insurance(Base):
    """Insurance model class."""

    __tablename__ = "insurance"
    id = Column(Integer, primary_key=True, nullable=False)
    name = Column(String(50), nullable=False)
    telephones = Column(ARRAY(String), nullable=False)


class Associate(Base):
    """Associate model class."""

    __tablename__ = "associate"
    id = Column(Integer, primary_key=True, nullable=False)
    name = Column(String(50), nullable=False)
    surnames = Column(String(100), nullable=False)
    telephones = Column(ARRAY(String), nullable=False)
    cars = relationship("Car", secondary=associate_car, back_populates="associate")
    created_at = Column(DateTime(timezone=True), default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=func.now(), onupdate=func.now(), nullable=False)
```

- [ ] **Step 2: Verify import**

```bash
python -c "from app.models.car import Car, Insurance, Associate; print('OK')"
```

Expected: `OK`

- [ ] **Step 3: Commit**

```bash
git add app/models/car.py
git commit -m "fix: fix associate_id type, widen status, remove owner columns, add image fields and archived_at to Car"
```

---

### Task 4: Fix `app/models/document.py`

**Files:**
- Modify: `app/models/document.py`

**What to add:**
- `category = Column(String(50), nullable=False)`
- `confidence = Column(Numeric(5, 4), nullable=True)` (0.0000–1.0000)
- `extracted_fields = Column(JSON, nullable=True)`
- `expiry_date = Column(DateTime(timezone=True), nullable=True)`

- [ ] **Step 1: Rewrite `app/models/document.py`**

```python
from sqlalchemy import JSON, Column, DateTime, Integer, Numeric, String
from sqlalchemy.sql import func

from app.database.base import Base


class Document(Base):
    """Document entity - stores all documents."""

    __tablename__ = "document"

    id = Column(Integer, primary_key=True, nullable=False)
    type = Column(String(20), nullable=False)
    url = Column(String(512), nullable=False)
    category = Column(String(50), nullable=False)
    confidence = Column(Numeric(5, 4), nullable=True)
    extracted_fields = Column(JSON, nullable=True)
    expiry_date = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=func.now(), onupdate=func.now(), nullable=False)
```

- [ ] **Step 2: Verify import**

```bash
python -c "from app.models.document import Document; print('OK')"
```

Expected: `OK`

- [ ] **Step 3: Commit**

```bash
git add app/models/document.py
git commit -m "feat: add category, confidence, extracted_fields and expiry_date to Document"
```

---

### Task 5: Fix `app/models/contract.py` — typo correction

**Files:**
- Modify: `app/models/contract.py`

**What to change:**
- `gurantee_amount` → `guarantee_amount`

- [ ] **Step 1: Edit `app/models/contract.py` line 17**

Replace:
```python
    gurantee_amount = Column(Numeric(12, 2), nullable=False)
```
With:
```python
    guarantee_amount = Column(Numeric(12, 2), nullable=False)
```

- [ ] **Step 2: Verify import**

```bash
python -c "from app.models.contract import Contract; print(Contract.guarantee_amount); print('OK')"
```

Expected: `<sqlalchemy column>` then `OK`

- [ ] **Step 3: Commit**

```bash
git add app/models/contract.py
git commit -m "fix: correct typo gurantee_amount -> guarantee_amount in Contract"
```

---

### Task 6: Fix `app/models/balance.py` — `transaction.car_id` FK

**Files:**
- Modify: `app/models/balance.py`

**What to change:**
- `car_id = Column(Integer, nullable=True)` → `car_id = Column(String(15), ForeignKey("car.id"), nullable=True)`
- Add `ForeignKey` import

- [ ] **Step 1: Rewrite `app/models/balance.py`**

```python
from sqlalchemy import Column, ForeignKey, Index, Integer, Numeric, String
from sqlalchemy.sql import func
from sqlalchemy.types import DateTime

from app.database.base import Base


class Transaction(Base):
    """transaction model class."""

    __tablename__ = "transaction"
    reference = Column(String(50), nullable=False, primary_key=True)
    date = Column(DateTime(timezone=True), default=func.now(), nullable=False)
    amount = Column(Numeric(12, 2), nullable=True)
    type = Column(String(10), nullable=True)
    description = Column(String(255), nullable=True)
    payment_method = Column(String(50), nullable=False)
    status = Column(String(10), nullable=False, default="PENDING")
    category = Column(String(100), nullable=True)
    car_id = Column(String(15), ForeignKey("car.id"), nullable=True)

    __table_args__ = (Index("ix_transaction_date", "date"),)
```

- [ ] **Step 2: Verify import**

```bash
python -c "from app.models.balance import Transaction; print('OK')"
```

Expected: `OK`

- [ ] **Step 3: Commit**

```bash
git add app/models/balance.py
git commit -m "fix: convert transaction.car_id to String(15) FK referencing car.id"
```

---

### Task 7: Register all CRM models in `app/models/__init__.py`

**Files:**
- Modify: `app/models/__init__.py`

**What to add:** Export every model class and every association `Table` object from all CRM model files so `Base.metadata` picks them all up (Alembic does `from app.models import *`).

- [ ] **Step 1: Rewrite `app/models/__init__.py`**

```python
from .balance import Transaction
from .car import Associate, Car, Insurance, associate_car, car_document_table
from .contract import Contract
from .document import Document
from .driver import (
    Driver,
    Guarantor,
    Reference,
    driver_document_table,
    driver_guarantor_table,
    driver_reference_table,
    guarantor_document_table,
    reference_document_table,
)
from .event import Event, Scheduler, event_document_table
from .incidence import Incidence, incidence_document_table
from .users import Permission, Role, User, role_permission_table

__all__ = [
    # Users
    "Role",
    "User",
    "Permission",
    "role_permission_table",
    # Balance
    "Transaction",
    # Car module
    "Car",
    "Insurance",
    "Associate",
    "car_document_table",
    "associate_car",
    # Driver module
    "Driver",
    "Reference",
    "Guarantor",
    "driver_document_table",
    "driver_guarantor_table",
    "driver_reference_table",
    "guarantor_document_table",
    "reference_document_table",
    # Shared
    "Document",
    "Contract",
    # Incidence
    "Incidence",
    "incidence_document_table",
    # Event
    "Event",
    "Scheduler",
    "event_document_table",
]
```

- [ ] **Step 2: Verify all models importable**

```bash
python -c "from app.models import *; print('All models imported OK')"
```

Expected: `All models imported OK`

- [ ] **Step 3: Commit**

```bash
git add app/models/__init__.py
git commit -m "feat: register all CRM models in __init__.py so Alembic detects them"
```

---

### Task 8: Write the Alembic migration

**Files:**
- Create: `alembic/versions/d1e2f3a4b5c6_register_crm_models.py`

**Dependencies:** Tasks 1–7 must be complete (all models must be correct before authoring the migration).

This migration:
1. Creates all CRM tables in dependency order
2. ALTERs `transaction.car_id` from `Integer` to `String(15)` with FK to `car.id`

The migration is hand-authored (not autogenerated) for full control.

- [ ] **Step 1: Create the migration file**

```python
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
```

- [ ] **Step 2: Verify Alembic recognizes the migration**

```bash
alembic history
```

Expected: `d1e2f3a4b5c6 -> (head)` appears in the list.

- [ ] **Step 3: Run upgrade on a clean database**

```bash
alembic upgrade head
```

Expected: No errors. All tables created.

- [ ] **Step 4: Inspect the tables (in psql or pgAdmin)**

```bash
psql $DATABASE_URL -c "\dt"
```

Expected: `associate`, `associate_car`, `car`, `car_document`, `contract`, `document`, `driver`, `driver_document`, `driver_guarantor`, `driver_reference`, `event`, `event_document`, `guarantor`, `guarantor_document`, `incidence`, `incidence_document`, `insurance`, `reference`, `reference_document`, `scheduler` all present.

- [ ] **Step 5: Run downgrade**

```bash
alembic downgrade -1
```

Expected: No errors. All CRM tables dropped, `transaction.car_id` reverted to Integer.

- [ ] **Step 6: Run upgrade again to leave DB in migrated state**

```bash
alembic upgrade head
```

- [ ] **Step 7: Run tests to verify coverage not broken**

```bash
pipenv run test
```

Expected: All tests pass, coverage ≥ 80%.

- [ ] **Step 8: Commit**

```bash
git add alembic/versions/d1e2f3a4b5c6_register_crm_models.py
git commit -m "feat: add Alembic migration to create all CRM tables and fix transaction.car_id FK"
```

---

## Self-Review

### Spec Coverage

| Spec requirement | Covered by |
|-----------------|-----------|
| Register all CRM models in `__init__.py` | Task 7 |
| Create `car`, `insurance`, `associate`, `associate_car` tables | Task 8 |
| Create `driver`, `guarantor`, `reference`, driver M2M tables | Task 8 |
| Create `document`, `contract`, `incidence`, `incidence_document`, `car_document` | Task 8 |
| `CarStatus` / `DriverStatus` enums | Task 1 |
| Widen status String(10) → String(20) | Tasks 2, 3 |
| Canonicalize `reference` table name | Task 2 |
| Fix `Contract.gurantee_amount` typo | Task 5 |
| Convert `transaction.car_id` to String(15) FK | Tasks 6, 8 |
| Remove `Car.owner_name` / `Car.owner_surnames` | Task 3 |
| Add `Car.archived_at` and `Driver.archived_at` | Tasks 3, 2 |
| Add `Document.category/confidence/extracted_fields/expiry_date` | Task 4 |
| Add `Car.agency_image`, `Car.photos`, `Driver.photo` | Tasks 3, 2 |
| `alembic upgrade head` clean | Task 8, Step 3 |
| `alembic downgrade` works | Task 8, Step 5 |
| Fix `associate_car.associate_id` type mismatch (Integer) | Task 3 |
