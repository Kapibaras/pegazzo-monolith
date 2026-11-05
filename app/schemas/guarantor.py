from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel

from app.schemas.address import AddressFieldsSchema


class GuarantorCreateSchema(BaseModel):
    """Request body for POST /management/drivers/{driver_id}/guarantors."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    name: str = Field(..., min_length=1, max_length=50)
    surnames: str = Field(..., min_length=1, max_length=100)
    telephones: list[Annotated[str, Field(min_length=1, max_length=20)]] = Field(default_factory=list)
    address_fields: AddressFieldsSchema
    relation: str = Field(..., min_length=1, max_length=50)


class GuarantorPatchSchema(BaseModel):
    """Request body for PATCH /management/guarantors/{guarantor_id}."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    name: str | None = Field(default=None, min_length=1, max_length=50)
    surnames: str | None = Field(default=None, min_length=1, max_length=100)
    telephones: list[Annotated[str, Field(min_length=1, max_length=20)]] | None = None
    address_fields: AddressFieldsSchema | None = None
    relation: str | None = Field(default=None, min_length=1, max_length=50)


class GuarantorResponseSchema(BaseModel):
    """Response schema for guarantor endpoints."""

    model_config = ConfigDict(from_attributes=True, alias_generator=to_camel, populate_by_name=True)

    id: int
    name: str
    surnames: str
    telephones: list[str]
    address: str
    address_fields: AddressFieldsSchema | None = None
    relation: str
    created_at: datetime
    updated_at: datetime
