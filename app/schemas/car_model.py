from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel


class CarModelCreateSchema(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    make: str = Field(..., min_length=1, max_length=50)
    model: str = Field(..., min_length=1, max_length=50)
    abbreviation: str = Field(..., min_length=1, max_length=10)


class CarModelItemSchema(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True, from_attributes=True)

    id: int
    model: str
    abbreviation: str


class CarModelGroupSchema(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    make: str
    models: list[CarModelItemSchema]


class CarModelResponseSchema(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True, from_attributes=True)

    id: int
    make: str
    model: str
    abbreviation: str
