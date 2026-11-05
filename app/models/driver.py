from sqlalchemy import JSON, Column, ForeignKey, Integer, String, Table
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

garage_document_table = Table(
    "garage_document",
    Base.metadata,
    Column("garage_id", Integer, ForeignKey("driver_garage.id"), primary_key=True, nullable=False),
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
    license_number = Column(String(20), nullable=False, unique=True, index=True)
    license_validity = Column(DateTime(timezone=True), default=func.now(), nullable=False)
    identification_number = Column(String(20), nullable=False, unique=True)
    address = Column(String(255), nullable=False)
    address_fields = Column(JSON, nullable=True)
    references = relationship("Reference", secondary=driver_reference_table)
    documents = relationship("Document", secondary=driver_document_table)
    guarantors = relationship("Guarantor", secondary=driver_guarantor_table)
    garages = relationship("DriverGarage", order_by="DriverGarage.id")
    photo = Column(String(512), nullable=True)
    archived_at = Column(DateTime(timezone=True), nullable=True)
    deleted_at = Column(DateTime(timezone=True), nullable=True)
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
    address_fields = Column(JSON, nullable=True)
    relation = Column(String(50), nullable=False)
    documents = relationship("Document", secondary=guarantor_document_table)
    created_at = Column(DateTime(timezone=True), default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=func.now(), onupdate=func.now(), nullable=False)


class DriverGarage(Base):
    """A garage of a driver. Its address proof is a document linked through `garage_document`."""

    __tablename__ = "driver_garage"
    id = Column(Integer, primary_key=True, nullable=False)
    driver_id = Column(String(15), ForeignKey("driver.id"), nullable=False, index=True)
    address = Column(String(255), nullable=False)
    address_fields = Column(JSON, nullable=True)
    documents = relationship("Document", secondary=garage_document_table)
    created_at = Column(DateTime(timezone=True), default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=func.now(), onupdate=func.now(), nullable=False)
