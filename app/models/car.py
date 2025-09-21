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
    Column("associate_id", String(15), ForeignKey("associate.id"), primary_key=True, nullable=False),
    Column("car_id", String(15), ForeignKey("car.id"), primary_key=True, nullable=False),
)


class Car(Base):
    """Car model class."""

    __tablename__ = "car"
    id = Column(String(15), primary_key=True, nullable=False)
    status = Column(String(10), nullable=False)
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
    owner_name = Column(String(50), nullable=False)
    owner_surnames = Column(String(100), nullable=False)
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
