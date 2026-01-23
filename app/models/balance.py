from sqlalchemy import Column, Index, Numeric, String
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

    __table_args__ = (Index("ix_transaction_date", "date"),)
