import math

from app.repositories.driver import DriverRepository
from app.schemas.car import PaginationSchema
from app.schemas.driver import DriverListQuerySchema, DriverListResponseSchema


class DriverService:
    """Business logic for driver operations."""

    def __init__(self, repository: DriverRepository):
        self.repository = repository

    def list_drivers(self, params: DriverListQuerySchema) -> DriverListResponseSchema:
        """Return a paginated, filtered and sorted list of drivers."""
        offset = (params.page - 1) * params.limit
        total = self.repository.count_drivers(
            status=params.status,
            search=params.search,
            archived=params.archived,
        )
        drivers = self.repository.list_drivers(
            status=params.status,
            search=params.search,
            archived=params.archived,
            sort_by=params.sort_by,
            sort_order=params.sort_order,
            limit=params.limit,
            offset=offset,
        )
        return DriverListResponseSchema(
            drivers=drivers,
            pagination=PaginationSchema(
                page=params.page,
                limit=params.limit,
                total=total,
                total_pages=0 if total == 0 else math.ceil(total / params.limit),
            ),
        )
