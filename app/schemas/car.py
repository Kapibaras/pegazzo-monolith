import datetime
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator
from pydantic.alias_generators import to_camel

from app.enum.balance import SortOrder
from app.enum.crm import CarSortBy, CarStatus
from app.schemas.types import RequestUTCDatetime

_CAMEL = ConfigDict(alias_generator=to_camel, populate_by_name=True)


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

    # Financing
    is_financed_liquidated: bool = Field(..., description="True if the financing is fully paid off")
    financing_agency: str | None = Field(default=None, min_length=1, max_length=100)
    financing_purchase_date: datetime.date | None = Field(default=None)
    financing_term_months: int | None = Field(default=None, ge=1)
    financing_remaining_amount: Decimal | None = Field(default=None, ge=0)

    # Optional
    features: Any | None = Field(default=None)
    details: Any | None = Field(default=None)

    @model_validator(mode="after")
    def check_financing_fields_required_when_not_liquidated(self) -> "CarSchema":
        """Financing details are required when isFinancedLiquidated is false."""
        if not self.is_financed_liquidated:
            missing = [
                f
                for f in [
                    "financing_agency",
                    "financing_purchase_date",
                    "financing_term_months",
                    "financing_remaining_amount",
                ]
                if getattr(self, f) is None
            ]
            if missing:
                raise ValueError(
                    f"Required when isFinancedLiquidated is false: {', '.join(missing)}",
                )
        return self

    # Insurance (required)
    insurance_provider_id: int = Field(..., description="FK to insurance table")
    policy_number: str = Field(..., min_length=1, max_length=30)
    policy_expiration_date: RequestUTCDatetime
    policy_type: str = Field(..., min_length=1, max_length=20)

    # Associate (optional)
    associate_id: int | None = Field(default=None, description="FK to associate table")


class CarListQuerySchema(BaseModel):
    """Query parameters for GET /management/cars."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    page: int = Field(default=1, ge=1, description="Page number starting at 1")
    limit: int = Field(default=10, ge=1, le=100, description="Records per page (max 100)")
    status: CarStatus | None = Field(default=None, description="Filter by status: ACTIVE, INACTIVE, IN_MAINTENANCE")
    search: str | None = Field(
        default=None,
        min_length=1,
        max_length=100,
        description=(
            "Fuzzy search over make, model and id. "
            "A 4-digit token in the text is treated as a year filter. "
            "Precedence: exact id > model > make."
        ),
    )
    year: str | None = Field(
        default=None,
        min_length=4,
        max_length=4,
        pattern=r"^\d{4}$",
        description="Exact year filter (e.g. 2022). Overrides any year token found in search.",
    )
    archived: bool = Field(default=False, description="If true, return only archived cars; otherwise active cars only")
    sort_by: CarSortBy = Field(default=CarSortBy.CREATED_AT, description="Field to sort by")
    sort_order: SortOrder = Field(default=SortOrder.DESC, description="Sort direction: asc or desc")


class CarSummarySchema(BaseModel):
    """Lightweight car summary returned in the list endpoint."""

    model_config = ConfigDict(from_attributes=True, alias_generator=to_camel, populate_by_name=True)

    id: str
    make: str
    model: str
    plate: str
    status: str
    year: str
    color: str
    agency_image: str | None = None


class PaginationSchema(BaseModel):
    """Pagination metadata."""

    page: int = Field(..., ge=1)
    limit: int = Field(..., ge=1, le=100)
    total: int = Field(..., ge=0)
    total_pages: int = Field(..., ge=0)

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)


class CarListResponseSchema(BaseModel):
    """Response for GET /management/cars."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    cars: list[CarSummarySchema] = Field(default_factory=list)
    pagination: PaginationSchema


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
    is_financed_liquidated: bool
    financing_agency: str | None = None
    financing_purchase_date: Any | None = None
    financing_term_months: int | None = None
    financing_remaining_amount: Any | None = None
    features: Any | None = None
    details: Any | None = None
    insurance_provider_id: int
    policy_number: str
    policy_expiration_date: Any
    policy_type: str
    agency_image: str | None = None
    photos: Any | None = None
    created_at: Any
    updated_at: Any


class InsuranceDetailSchema(BaseModel):
    """Insurance provider plus policy fields for the car detail response."""

    model_config = _CAMEL

    id: int
    name: str
    policy_number: str
    policy_expiration_date: Any
    policy_type: str


class AssociateDetailSchema(BaseModel):
    """Associate linked to the car."""

    model_config = _CAMEL

    id: int
    name: str
    surnames: str
    telephones: list[str]


class AssignedDriverSchema(BaseModel):
    """Brief driver info derived from the active contract."""

    model_config = _CAMEL

    id: str
    name: str
    surnames: str


class DocumentDetailSchema(BaseModel):
    """Document with a temporary presigned GET URL and computed expiry status."""

    model_config = _CAMEL

    id: int
    type: str
    category: str
    expiry_date: Any | None = None
    url: str
    expiry_status: str | None = None


class CarDetailResponseSchema(BaseModel):
    """Full car detail response."""

    model_config = _CAMEL

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
    is_financed_liquidated: bool
    financing_agency: str | None = None
    financing_purchase_date: Any | None = None
    financing_term_months: int | None = None
    financing_remaining_amount: Any | None = None
    features: Any | None = None
    details: Any | None = None
    agency_image: str | None = None
    photos: list[str] | None = None
    archived_at: Any | None = None
    created_at: Any
    updated_at: Any
    insurance: InsuranceDetailSchema
    associate: AssociateDetailSchema | None = None
    documents: list[DocumentDetailSchema] = Field(default_factory=list)
    assigned_driver: AssignedDriverSchema | None = None
