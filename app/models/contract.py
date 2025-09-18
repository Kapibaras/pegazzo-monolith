from sqlalchemy import Column, Date, ForeignKey, Numeric, String
from sqlalchemy.orm import relationship

from app.database.base import Base


class Contract(Base):
    """Contract entity - links drivers with cars."""

    __tablename__ = "contract"

    id = Column(String(15), primary_key=True, nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    type = Column(String(10), nullable=False)
    amount = Column(Numeric(12, 2), nullable=False)
    gurantee_amount = Column(Numeric(12, 2), nullable=False)
    sanction_amount = Column(Numeric(12, 2), nullable=True)
    due_amount = Column(Numeric(12, 2), nullable=True)
    signed_document_in = Column(String(512), nullable=True)
    signed_document_out = Column(String(512), nullable=True)
    signed_checklist_in = Column(String(512), nullable=True)
    signed_checklist_out = Column(String(512), nullable=True)
    car_id = Column(String(15), ForeignKey("car.id"), nullable=True)
    driver_id = Column(String(15), ForeignKey("driver.id"), nullable=True)
    car = relationship("Car")
    driver = relationship("Driver")
