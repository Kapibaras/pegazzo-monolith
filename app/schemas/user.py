from pydantic import BaseModel, Field

# * MODEL SCHEMAS * #


class UserSchema(BaseModel):
    """
    Schema for user-related operations.
    """

    username: str = Field(..., description="Username of the user")
    name: str = Field(..., description="Name of the user")
    surnames: str = Field(..., description="Surnames of the user")
    role_name: str = Field(..., description="Role of the user", alias="role")

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
        )


# * BODY SCHEMAS * #


class UserCreateSchema(BaseModel):
    username: str = Field(..., description="Username of the user")
    name: str = Field(..., description="Name of the user")
    surnames: str = Field(..., description="Surnames of the user")
    password: str = Field(..., description="Password of the user")
    role_id: int = Field(..., description="Role ID of the user", alias="roleId")


# * RESPONSE SCHEMAS * #

# Add schemas..
