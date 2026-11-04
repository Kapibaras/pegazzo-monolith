from pydantic import BaseModel, Field

from app.schemas.car import CarSummarySchema


class AssociateSchema(BaseModel):
    """Schema for creating an associate."""

    name: str = Field(..., min_length=1, max_length=50)
    surnames: str = Field(..., min_length=1, max_length=100)
    telephones: list[str] | None = Field(default=None)


class AssociatePatchSchema(BaseModel):
    """Schema for partially updating an associate."""

    name: str | None = Field(default=None, min_length=1, max_length=50)
    surnames: str | None = Field(default=None, min_length=1, max_length=100)
    telephones: list[str] | None = Field(default=None)


class AssociateResponseSchema(BaseModel):
    """Schema for associate response."""

    id: int
    name: str
    surnames: str
    telephones: list[str] | None
    car_count: int = Field(0, description="Number of cars linked to the associate")

    model_config = {"from_attributes": True}


class AssociateDetailResponseSchema(AssociateResponseSchema):
    """Schema for a single associate, including the cars linked to it."""

    cars: list[CarSummarySchema] = Field(default_factory=list, description="Cars linked to the associate")
