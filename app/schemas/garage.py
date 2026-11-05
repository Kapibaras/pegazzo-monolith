from datetime import datetime

from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel

from app.schemas.address import AddressFieldsSchema


class GarageCreateSchema(BaseModel):
    """Request body for POST /management/drivers/{driver_id}/garages."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    address_fields: AddressFieldsSchema


class GaragePatchSchema(BaseModel):
    """Request body for PATCH /management/drivers/{driver_id}/garages/{garage_id}."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    address_fields: AddressFieldsSchema


class GarageResponseSchema(BaseModel):
    """Response schema for the garage endpoints."""

    model_config = ConfigDict(from_attributes=True, alias_generator=to_camel, populate_by_name=True)

    id: int
    address: str
    address_fields: AddressFieldsSchema | None = None
    created_at: datetime
    updated_at: datetime
