from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field

from app.auth import Role

# * MODEL SCHEMAS * #


class UserSchema(BaseModel):
    """Schema for a user."""

    username: str = Field(..., description="Username of the user")
    name: str = Field(..., description="Name of the user")
    surnames: str = Field(..., description="Surnames of the user")
    role_name: Role = Field(..., alias="role", description="Role of the user")
    created_at: datetime = Field(..., description="User creation timestamp")
    updated_at: datetime = Field(..., description="User update timestamp")

    class Config:
        """Pydantic model configuration."""

        orm_mode = True
        allow_population_by_field_name = True

    @classmethod
    def from_orm(cls, obj):
        """Convert a User model instance to a UserSchema."""
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
    """Schema for creating a user."""

    username: str = Field(..., description="Username of the user")
    name: str = Field(..., description="Name of the user")
    surnames: str = Field(..., description="Surnames of the user")
    password: str = Field(..., description="Password of the user")
    role: Role = Field(..., description="Role of the user")


class UserUpdateSchema(BaseModel):
    """Schema for updating a user."""

    name: str = Field(..., description="Name of the user")
    surnames: str = Field(..., description="Surnames of the user")
    role: Role = Field(..., description="Role of the user")


class UserUpdatePasswordSchema(BaseModel):
    """Schema for updating a user's password (admin reset)."""

    new_password: str = Field(..., min_length=6, description="New password for the user")


# * RESPONSE SCHEMAS * #


class PermissionsResponse(BaseModel):
    """Schema for permissions responses."""

    role: str = Field(..., description="Role of the user")
    permissions: list[str] = Field(..., description="Permissions of the user")


class ActionSuccess(BaseModel):
    """Schema for successful action responses (e.g., DELETE).

    Attributes:
        message (str): A descriptive message indicating the result of the action.
        extra_data (Any, optional): Additional data relevant to the action. Defaults to None.

    """

    message: str = Field(
        ...,
        description="Message indicating the action was successfully performed",
        example="User deleted successfully.",
    )
    extra_data: Optional[Any] = Field(default=None, description="Additional data relevant to the action")
