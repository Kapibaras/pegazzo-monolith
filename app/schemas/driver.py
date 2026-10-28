from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel

from app.enum.balance import SortOrder
from app.enum.crm import DriverSortBy, DriverStatus
from app.schemas.car import DocumentDetailSchema, PaginationSchema
from app.schemas.types import RequestUTCDatetime

_CAMEL = ConfigDict(from_attributes=True, alias_generator=to_camel, populate_by_name=True)


class DriverListQuerySchema(BaseModel):
    """Query parameters for GET /management/drivers."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    page: int = Field(default=1, ge=1, description="Page number starting at 1")
    limit: int = Field(default=10, ge=1, le=100, description="Records per page (max 100)")
    status: DriverStatus | None = Field(default=None, description="Filter by status: ACTIVE, INACTIVE, SUSPENDED")
    search: str | None = Field(
        default=None,
        min_length=1,
        max_length=100,
        description="Fuzzy search over name, surnames and id. Precedence: exact id > surnames > name.",
    )
    archived: bool = Field(default=False, description="If true, return only archived drivers; otherwise active only")
    sort_by: DriverSortBy = Field(default=DriverSortBy.CREATED_AT, description="Field to sort by")
    sort_order: SortOrder = Field(default=SortOrder.DESC, description="Sort direction: asc or desc")


class DriverSummarySchema(BaseModel):
    """Lightweight driver summary returned in the list endpoint."""

    model_config = ConfigDict(from_attributes=True, alias_generator=to_camel, populate_by_name=True)

    id: str
    name: str
    surnames: str
    status: str
    photo: str | None = None


class DriverListResponseSchema(BaseModel):
    """Response for GET /management/drivers."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    drivers: list[DriverSummarySchema] = Field(default_factory=list)
    pagination: PaginationSchema


class DriverCreateSchema(BaseModel):
    """Request body for POST /management/drivers."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    id: str = Field(..., max_length=15)
    name: str = Field(..., max_length=50)
    surnames: str = Field(..., max_length=100)
    status: DriverStatus
    telephones: list[str] = Field(..., min_length=1)
    license_number: str = Field(..., max_length=20)
    license_validity: RequestUTCDatetime
    identification_number: str = Field(..., max_length=20)
    address: str = Field(..., max_length=255)
    garage_address: list[str] = Field(..., min_length=1)


class _DriverBaseSchema(BaseModel):
    """Shared driver fields for response schemas."""

    model_config = _CAMEL

    id: str
    name: str
    surnames: str
    status: str
    telephones: list[str]
    license_number: str
    license_validity: datetime
    identification_number: str
    address: str
    garage_address: list[str]
    photo: str | None = None
    created_at: datetime
    updated_at: datetime


class DriverResponseSchema(_DriverBaseSchema):
    """Response for POST /management/drivers."""


class GuarantorDetailSchema(BaseModel):
    """Guarantor with their documents."""

    model_config = _CAMEL

    id: int
    name: str
    surnames: str
    telephones: list[str]
    address: str
    relation: str
    documents: list[DocumentDetailSchema] = Field(default_factory=list)


class AssignedCarSchema(BaseModel):
    """Brief car info derived from the active contract."""

    model_config = _CAMEL

    id: str
    make: str
    model: str
    plate: str
    agency_image: str | None = None


class DriverDetailResponseSchema(_DriverBaseSchema):
    """Full driver detail response."""

    archived_at: datetime | None = None
    documents: list[DocumentDetailSchema] = Field(default_factory=list)
    guarantors: list[GuarantorDetailSchema] = Field(default_factory=list)
    assigned_car: AssignedCarSchema | None = None
