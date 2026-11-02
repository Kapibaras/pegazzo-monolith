from datetime import UTC, datetime

from app.models.driver import Guarantor

_SEED_GUARANTORS = [
    Guarantor(
        id=1,
        name="Carlos",
        surnames="García López",
        telephones=["+521234567890"],
        address="Calle 1 #100",
        relation="father",
        created_at=datetime(2026, 1, 15, tzinfo=UTC),
        updated_at=datetime(2026, 1, 15, tzinfo=UTC),
    ),
    Guarantor(
        id=2,
        name="Rosa",
        surnames="López García",
        telephones=[],
        address="Av. Principal #50",
        relation="mother",
        created_at=datetime(2026, 2, 20, tzinfo=UTC),
        updated_at=datetime(2026, 2, 20, tzinfo=UTC),
    ),
]


class GuarantorRepositoryMock:
    """In-memory mock for GuarantorRepository."""

    def __init__(self):
        self.guarantors: list[Guarantor] = []
        self._next_id = 3
        self.driver_links: dict[str, set[int]] = {}
        self.document_keys: dict[int, list[str]] = {}
        self.reset()

    def reset(self):
        self.guarantors = [self._copy(g) for g in _SEED_GUARANTORS]
        self._next_id = 3
        self.driver_links = {}
        self.document_keys = {}

    @staticmethod
    def _copy(g: Guarantor) -> Guarantor:
        return Guarantor(
            id=g.id,
            name=g.name,
            surnames=g.surnames,
            telephones=list(g.telephones),
            address=g.address,
            relation=g.relation,
            created_at=g.created_at,
            updated_at=g.updated_at,
        )

    def get_by_id(self, guarantor_id: int) -> Guarantor | None:
        return next((g for g in self.guarantors if g.id == guarantor_id), None)

    def create_and_link(self, guarantor: Guarantor, driver_id: str) -> Guarantor:
        now = datetime.now(UTC)
        guarantor.id = self._next_id
        self._next_id += 1
        if guarantor.created_at is None:
            guarantor.created_at = now
        if guarantor.updated_at is None:
            guarantor.updated_at = now
        self.guarantors.append(guarantor)
        self.driver_links.setdefault(driver_id, set()).add(guarantor.id)
        return guarantor

    def update(self, guarantor: Guarantor) -> Guarantor:
        guarantor.updated_at = datetime.now(UTC)
        return guarantor

    def unlink_and_delete_if_orphan(self, driver_id: str, guarantor: Guarantor) -> list[str]:
        self.unlink_from_driver(driver_id, guarantor.id)
        if self.count_linked_drivers(guarantor.id):
            return []
        self.guarantors = [g for g in self.guarantors if g.id != guarantor.id]
        return self.document_keys.pop(guarantor.id, [])

    def link_to_driver(self, driver_id: str, guarantor_id: int) -> None:
        self.driver_links.setdefault(driver_id, set()).add(guarantor_id)

    def unlink_from_driver(self, driver_id: str, guarantor_id: int) -> None:
        if driver_id in self.driver_links:
            self.driver_links[driver_id].discard(guarantor_id)

    def is_linked_to_driver(self, driver_id: str, guarantor_id: int) -> bool:
        return guarantor_id in self.driver_links.get(driver_id, set())

    def count_guarantors_for_driver(self, driver_id: str, *, lock: bool = False) -> int:  # noqa: ARG002
        return len(self.driver_links.get(driver_id, set()))

    def count_linked_drivers(self, guarantor_id: int) -> int:
        return sum(1 for links in self.driver_links.values() if guarantor_id in links)
