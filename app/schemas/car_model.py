from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel


class CarModelCreateSchema(BaseModel):
    """Request body for creating a new car model catalog entry."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    make: str = Field(..., min_length=1, max_length=50)
    model: str = Field(..., min_length=1, max_length=50)
    abbreviation: str = Field(..., min_length=1, max_length=10)


class CarModelItemSchema(BaseModel):
    """A single model entry within a grouped catalog response."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True, from_attributes=True)

    id: int
    model: str
    abbreviation: str


class CarModelGroupSchema(BaseModel):
    """Catalog entries for a single make, used in the grouped list response."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    make: str
    models: list[CarModelItemSchema]


class CarModelResponseSchema(BaseModel):
    """Response body for create/get car model endpoints."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True, from_attributes=True)

    id: int
    make: str
    model: str
    abbreviation: str
