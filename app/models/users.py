from app.database.base import Base
from sqlalchemy import Column, Integer, String, Table, ForeignKey
from sqlalchemy.orm import relationship

role_permission_table = Table(
    "role_permission",
    Base.metadata,
    Column("role_id", Integer, ForeignKey("role.id")),
    Column("permission_id", Integer, ForeignKey("permission.id")),
)


class Role(Base):
    __tablename__ = "role"
    id = Column(
        Integer,
        primary_key=True,
        index=True
    )
    name = Column(
        String(50),
        nullable=False
    )
    permissions = relationship(
        "Permission",
        secondary=role_permission_table
    )


class User(Base):
    __tablename__ = "users"
    username = Column(
        String(30),
        primary_key=True,
        unique=True,
        index=True,
        nullable=False
    )
    name = Column(
        String(50),
        nullable=False
    )
    surnames = Column(
        String(100),
        nullable=False
    )
    password = Column(
        String(128),
        nullable=False
    )
    role_id = Column(
        Integer,
        ForeignKey("role.id"),
        nullable=False
    )
    role = relationship("Role")


class Permission(Base):
    __tablename__ = "permission"
    id = Column(
        Integer,
        primary_key=True,
        index=True
    )
    name = Column(
        String(50),
        nullable=False
    )
