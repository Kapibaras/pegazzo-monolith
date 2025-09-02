from sqlalchemy import Column, ForeignKey, Integer, String, Table, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.types import DateTime

from app.database.base import Base

incidence_document_table = Table(
    "incidence_document",
    Base.metadata,
    Column("incidence_id", Integer, ForeignKey("incidence.id"), primary_key=True, nullable=False),
    Column("document_id", Integer, ForeignKey("document.id"), primary_key=True, nullable=False),
)


class Incidence(Base):
    """Incidence model class."""

    __tablename__ = "incidence"
    id = Column(Integer, primary_key=True, nullable=False)
    type = Column(String(50), nullable=False)
    description = Column(Text, nullable=False)
    location = Column(String(255), nullable=True)
    odometer = Column(Integer, nullable=True)
    occurred_at = Column(DateTime(timezone=True))
    car_id = Column(String(15), ForeignKey("car.id"), nullable=True)
    driver_id = Column(String(15), ForeignKey("driver.id"), nullable=True)
    car = relationship("Car")
    driver = relationship("Driver")
    created_at = Column(DateTime(timezone=True), default=func.now(), nullable=False)
