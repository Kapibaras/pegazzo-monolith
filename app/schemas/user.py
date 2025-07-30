from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field

# * ENUMS * #


class RoleEnum(str, Enum):
    admin = "admin"
    user = "user"


# * MODEL SCHEMAS * #


class UserSchema(BaseModel):
    """
    Schema for user-related operations.
    """

    username: str = Field(..., description="Username of the user")
    name: str = Field(..., description="Name of the user")
    surnames: str = Field(..., description="Surnames of the user")
    role_name: RoleEnum = Field(..., description="Role of the user", alias="role")
    created_at: datetime = Field(..., description="User creation timestamp")
    updated_at: datetime = Field(..., description="User update timestamp")

    class Config:
        orm_mode = True
        allow_population_by_field_name = True

    @classmethod
    def from_orm(cls, obj):
        return cls(
            username=obj.username,
            name=obj.name,
            surnames=obj.surnames,
            role=obj.role.name,
            created_at=obj.created_at,
            updated_at=obj.updated_at,
        )


# * BODY SCHEMAS * #


class UserCreateSchema(BaseModel):
    username: str = Field(..., description="Username of the user")
    name: str = Field(..., description="Name of the user")
    surnames: str = Field(..., description="Surnames of the user")
    password: str = Field(..., description="Password of the user")
    role: RoleEnum = Field(..., description="Role of the user")


class UserUpdateSchema(BaseModel):
    name: str = Field(..., description="Name of the user")
    surnames: str = Field(..., description="Surnames of the user")
    role: RoleEnum = Field(..., description="Role of the user")


# * RESPONSE SCHEMAS * #


class ActionSuccess(BaseModel):
    """
    Schema para respuestas exitosas de acciones (como DELETE).

    Atributos:
        message (str): Un mensaje descriptivo indicando el resultado de la acción.
    """

    message: str = Field(
        ..., description="Mensaje indicando que la acción se realizó exitosamente", example="User deleted successfully."
    )


# Add schemas..
