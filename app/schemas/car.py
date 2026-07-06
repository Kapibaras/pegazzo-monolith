from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel

from app.enum.crm import CarStatus
from app.schemas.types import RequestUTCDatetime


class CarSchema(BaseModel):
    """Schema for creating a car."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    # Identity
    id: str = Field(..., min_length=1, max_length=15, description="Unique car identifier")
    make: str = Field(..., min_length=1, max_length=50)
    model: str = Field(..., min_length=1, max_length=50)
    year: str = Field(..., min_length=4, max_length=4)
    color: str = Field(..., min_length=1, max_length=30)
    status: CarStatus = Field(..., description="Car status: ACTIVE, INACTIVE or IN_MAINTENANCE")

    # Technical
    vin: str = Field(..., min_length=1, max_length=17, description="Vehicle Identification Number (unique)")
    plate: str = Field(..., min_length=1, max_length=10, description="License plate (unique)")
    body_type: str = Field(..., min_length=1, max_length=30)
    engine_type: str = Field(..., min_length=1, max_length=30)
    transmission: str = Field(..., min_length=1, max_length=20)
    engine_serial_number: str = Field(..., min_length=1, max_length=30)
    odometer: int = Field(..., ge=0)
    doors_number: int = Field(..., ge=1)
    passengers_number: int = Field(..., ge=1)
    tire_specification: str = Field(..., min_length=1, max_length=20)

    # Registry / values
    unit_value: float = Field(..., ge=0)
    unit_billing_value: float = Field(..., ge=0)
    bill_number: str = Field(..., min_length=1, max_length=30)
    public_vehicle_registry: str = Field(..., min_length=1, max_length=30)
    alta_public_vehicle_registry: RequestUTCDatetime

    # Battery
    battery_model: str = Field(..., min_length=1, max_length=20)
    battery_serial_number: str = Field(..., min_length=1, max_length=30)
    battery_date: RequestUTCDatetime

    # Owner
    legal_owner_name: str = Field(..., min_length=1, max_length=50)
    legal_owner_surnames: str = Field(..., min_length=1, max_length=100)
    financed_status: str = Field(..., min_length=1, max_length=20)

    # Optional
    features: Optional[Any] = Field(default=None)
    details: Optional[Any] = Field(default=None)

    # Insurance (required)
    insurance_provider_id: int = Field(..., description="FK to insurance table")
    policy_number: str = Field(..., min_length=1, max_length=30)
    policy_expiration_date: RequestUTCDatetime
    policy_type: str = Field(..., min_length=1, max_length=20)

    # Associate (optional)
    associate_id: Optional[int] = Field(default=None, description="FK to associate table")


class CarResponseSchema(BaseModel):
    """Schema for car response."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True, from_attributes=True)

    id: str
    make: str
    model: str
    year: str
    color: str
    status: str
    vin: str
    plate: str
    body_type: str
    engine_type: str
    transmission: str
    engine_serial_number: str
    odometer: int
    doors_number: int
    passengers_number: int
    tire_specification: str
    unit_value: float
    unit_billing_value: float
    bill_number: str
    public_vehicle_registry: str
    alta_public_vehicle_registry: Any
    battery_model: str
    battery_serial_number: str
    battery_date: Any
    legal_owner_name: str
    legal_owner_surnames: str
    financed_status: str
    features: Optional[Any] = None
    details: Optional[Any] = None
    insurance_provider_id: int
    policy_number: str
    policy_expiration_date: Any
    policy_type: str
    agency_image: Optional[str] = None
    photos: Optional[Any] = None
    created_at: Any
    updated_at: Any
