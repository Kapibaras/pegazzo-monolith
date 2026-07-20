from typing import Optional

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel


class InsuranceSchema(BaseModel):
    """Schema for creating an insurance provider."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    name: str = Field(..., min_length=1, max_length=50)
    telephones: Optional[list[str]] = Field(default=None)


class InsurancePatchSchema(BaseModel):
    """Schema for partially updating an insurance provider."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    name: Optional[str] = Field(default=None, min_length=1, max_length=50)
    telephones: Optional[list[str]] = Field(default=None)


class InsuranceResponseSchema(BaseModel):
    """Schema for insurance provider response."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True, from_attributes=True)

    id: int
    name: str
    telephones: Optional[list[str]] = None
