from sqlalchemy import Column, ForeignKey, Integer, String, Table
from sqlalchemy.dialects.postgresql import ARRAY
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

references_document_table = Table(
    "references_document",
    Base.metadata,
    Column("references_id", Integer, ForeignKey("references.id"), primary_key=True, nullable=False),
    Column("document_id", Integer, ForeignKey("document.id"), primary_key=True, nullable=False),
)


class Driver(Base):
    """Driver model class."""

    __tablename__ = "driver"
    id = Column(String(15), primary_key=True, nullable=False)
    status = Column(String(10), nullable=False)
    name = Column(String(50), nullable=False)
    surnames = Column(String(100), nullable=False)
    telephones = Column(ARRAY(String(20)), nullable=False)
    license_number = Column(String(20), nullable=False)
    license_validity = Column(DateTime(timezone=True), default=func.now(), nullable=False)
    identification_number = Column(String(20), nullable=False)
    address = Column(String(255), nullable=False)
    garage_address = Column(ARRAY(String(255)), nullable=False)
    created_at = Column(DateTime(timezone=True), default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=func.now(), onupdate=func.now(), nullable=False)


class References(Base):
    """References model class."""

    __tablename__ = "references"
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
    created_at = Column(DateTime(timezone=True), default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=func.now(), onupdate=func.now(), nullable=False)
