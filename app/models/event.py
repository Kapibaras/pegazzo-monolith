from sqlalchemy import Column, ForeignKey, Integer, String, Table, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.types import DateTime

from app.database.base import Base

event_document_table = Table(
    "event_document",
    Base.metadata,
    Column("event_id", Integer, ForeignKey("event.id"), primary_key=True, nullable=False),
    Column("document_id", Integer, ForeignKey("document.id"), primary_key=True, nullable=False),
)


class Event(Base):
    """Event model class."""

    __tablename__ = "event"
    id = Column(Integer, primary_key=True, nullable=False)
    category = Column(String(20), nullable=False)
    description = Column(Text, nullable=True)
    car_id = Column(String(15), ForeignKey("car.id"), nullable=True)
    driver_id = Column(String(15), ForeignKey("driver.id"), nullable=True)
    car = relationship("Car")
    driver = relationship("Driver")
    created_at = Column(DateTime(timezone=True), default=func.now(), nullable=False)
    to_resolve_at = Column(DateTime(timezone=True), nullable=True)
    accepted_at = Column(DateTime(timezone=True), nullable=True)


class Scheduler(Base):
    """Scheduler model class."""

    __tablename__ = "scheduler"
    id = Column(Integer, primary_key=True, nullable=False)
    category = Column(String(20), nullable=False)
    description = Column(Text, nullable=True)
    interval = Column(String(20), nullable=False)
    interval_count = Column(Integer, nullable=False)
    created_at = Column(DateTime(timezone=True), default=func.now(), nullable=False)
    last_launched_at = Column(DateTime(timezone=True), nullable=True)
