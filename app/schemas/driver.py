from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel

from app.enum.balance import SortOrder
from app.enum.crm import DriverSortBy, DriverStatus
from app.schemas.car import PaginationSchema


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
