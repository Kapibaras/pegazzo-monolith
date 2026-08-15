from sqlalchemy import Column, Integer, String, UniqueConstraint

from app.database.base import Base


class CarModel(Base):
    """CarModel catalog — maps (make, model) to an abbreviation used in the internal folio."""

    __tablename__ = "car_model"
    __table_args__ = (UniqueConstraint("make", "model", name="uq_car_model_make_model"),)

    id = Column(Integer, primary_key=True, nullable=False)
    make = Column(String(50), nullable=False)
    model = Column(String(50), nullable=False)
    abbreviation = Column(String(10), nullable=False)
