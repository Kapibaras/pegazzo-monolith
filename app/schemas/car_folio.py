from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel


class CarFolioRequestSchema(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    associate_id: int = Field(..., description="Associate who funded the car")
    legal_owner_is_pegazzo: bool = Field(..., description="True if Pegazzo is the legal owner")
    make: str = Field(..., max_length=50)
    model: str = Field(..., max_length=50)
    transmission: str = Field(..., max_length=20)


class CarFolioResponseSchema(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    folio: str
