from datetime import UTC, datetime

from app.enum.balance import SortOrder
from app.enum.crm import DriverSortBy, DriverStatus
from app.models.contract import Contract
from app.models.document import Document
from app.models.driver import Driver

_SEED_DRIVERS = [
    Driver(
        id="DRV-001",
        status=DriverStatus.ACTIVE,
        name="Luis",
        surnames="García López",
        telephones=["+521234567890"],
        license_number="LIC001",
        license_validity=datetime(2027, 6, 1, tzinfo=UTC),
        identification_number="ID001",
        address="Calle 1 #100",
        garage_address=["Calle 2 #200"],
        photo="https://images.example.com/drv001.jpg",
        archived_at=None,
        created_at=datetime(2026, 1, 15, tzinfo=UTC),
        updated_at=datetime(2026, 1, 15, tzinfo=UTC),
    ),
    Driver(
        id="DRV-002",
        status=DriverStatus.INACTIVE,
        name="María",
        surnames="Hernández Ruiz",
        telephones=["+529876543210"],
        license_number="LIC002",
        license_validity=datetime(2026, 12, 1, tzinfo=UTC),
        identification_number="ID002",
        address="Av. Principal #50",
        garage_address=["Av. Secundaria #60"],
        photo=None,
        archived_at=None,
        created_at=datetime(2026, 2, 20, tzinfo=UTC),
        updated_at=datetime(2026, 2, 20, tzinfo=UTC),
    ),
    Driver(
        id="DRV-003",
        status=DriverStatus.ACTIVE,
        name="Pedro",
        surnames="Martínez Soto",
        telephones=["+525551112222"],
        license_number="LIC003",
        license_validity=datetime(2027, 3, 1, tzinfo=UTC),
        identification_number="ID003",
        address="Blvd. Norte #300",
        garage_address=["Calle Sur #400"],
        photo=None,
        archived_at=datetime(2026, 6, 1, tzinfo=UTC),
        created_at=datetime(2026, 3, 10, tzinfo=UTC),
        updated_at=datetime(2026, 6, 1, tzinfo=UTC),
    ),
]


class DriverRepositoryMock:
    """In-memory mock for DriverRepository."""

    def __init__(self):
        self.drivers: list[Driver] = []
        self.driver_documents: dict[str, list[Document]] = {}
        self.contracts: list[Contract] = []
        self.reset()

    def reset(self):
        self.drivers = [self._copy(d) for d in _SEED_DRIVERS]
        self.driver_documents = {}
        self.contracts = []

    @staticmethod
    def _copy(d: Driver) -> Driver:
        driver = Driver(
            id=d.id,
            status=d.status,
            name=d.name,
            surnames=d.surnames,
            telephones=list(d.telephones),
            license_number=d.license_number,
            license_validity=d.license_validity,
            identification_number=d.identification_number,
            address=d.address,
            garage_address=list(d.garage_address),
            photo=d.photo,
            archived_at=d.archived_at,
            created_at=d.created_at,
            updated_at=d.updated_at,
        )
        driver.guarantors = list(d.guarantors)
        return driver

    def _filter(self, status: DriverStatus | None, search: str | None, archived: bool) -> list[Driver]:
        # NOTE: This mock uses substring matching for search. The real repository
        # uses PostgreSQL word_similarity (fuzzy). Behavior may diverge on edge cases.
        result = [
            d
            for d in self.drivers
            if not (archived and d.archived_at is None) and not (not archived and d.archived_at is not None) and (not status or d.status == status)
        ]

        if not search:
            return result

        text = search.strip().lower()
        if not text:
            return result

        id_matches = [d for d in result if d.id.lower() == text]
        if id_matches:
            return id_matches

        surname_matches = [d for d in result if text in d.surnames.lower()]
        if surname_matches:
            return surname_matches

        return [d for d in result if text in d.name.lower()]

    def count_drivers(self, status: DriverStatus | None, search: str | None, archived: bool) -> int:
        return len(self._filter(status, search, archived))

    def get_by_id(self, driver_id: str) -> Driver | None:
        return next((d for d in self.drivers if d.id == driver_id), None)

    def get_by_identification_number(self, identification_number: str) -> Driver | None:
        return next((d for d in self.drivers if d.identification_number == identification_number), None)

    def get_by_license_number(self, license_number: str) -> Driver | None:
        return next((d for d in self.drivers if d.license_number == license_number), None)

    def get_driver_documents(self, driver_id: str) -> list[Document]:
        return self.driver_documents.get(driver_id, [])

    def get_active_contract_for_driver(self, driver_id: str) -> Contract | None:
        today = datetime.now(tz=UTC).date()
        return next(
            (
                c
                for c in self.contracts
                if c.driver_id == driver_id and c.start_date <= today and c.end_date >= today
            ),
            None,
        )

    def create_driver(self, driver: Driver) -> Driver:
        now = datetime.now(UTC)
        if driver.created_at is None:
            driver.created_at = now
        if driver.updated_at is None:
            driver.updated_at = now
        self.drivers.append(driver)
        return driver

    def list_drivers(
        self,
        status: DriverStatus | None,
        search: str | None,
        archived: bool,
        sort_by: DriverSortBy,
        sort_order: SortOrder,
        limit: int,
        offset: int,
    ) -> list[Driver]:
        drivers = self._filter(status, search, archived)
        reverse = sort_order == SortOrder.DESC

        def _sort_key(d):
            return getattr(d, sort_by, "") or ""

        drivers.sort(key=_sort_key, reverse=reverse)
        return drivers[offset : offset + limit]
