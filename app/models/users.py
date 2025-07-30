from sqlalchemy import Column, ForeignKey, Integer, String, Table
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.types import DateTime

from app.database.base import Base

role_permission_table = Table(
    "role_permission",
    Base.metadata,
    Column("role_id", Integer, ForeignKey("role.id"), primary_key=True),
    Column("permission_id", Integer, ForeignKey("permission.id"), primary_key=True),
)


class Role(Base):
    """Role model class."""

    __tablename__ = "role"
    id = Column(Integer, primary_key=True)
    name = Column(String(50), nullable=False)
    permissions = relationship("Permission", secondary=role_permission_table)


class User(Base):
    """User model class."""

    __tablename__ = "user"
    username = Column(String(30), primary_key=True)
    name = Column(String(50), nullable=False)
    surnames = Column(String(100), nullable=False)
    password = Column(String(128), nullable=False)
    role_id = Column(Integer, ForeignKey("role.id"), nullable=False)
    role = relationship("Role")
    created_at = Column(DateTime(timezone=True), default=func.now())
    updated_at = Column(DateTime(timezone=True), default=func.now(), onupdate=func.now())


class Permission(Base):
    """Permission model class."""

    __tablename__ = "permission"
    id = Column(Integer, primary_key=True)
    name = Column(String(50), nullable=False)
