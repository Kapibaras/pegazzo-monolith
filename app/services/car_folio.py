from app.errors.car import AssociateNotFoundException, CarModelNotFoundException
from app.repositories.car import CarRepository
from app.repositories.car_model import CarModelRepository
from app.schemas.car_folio import CarFolioRequestSchema, CarFolioResponseSchema


def _owner_prefix(is_us_owner: bool, legal_owner_is_pegazzo: bool) -> str:
    if legal_owner_is_pegazzo:
        return "PG"
    return "US" if is_us_owner else "S"


def _associate_initials(name: str, surnames: str) -> str:
    """Return initials: first letter of first given name + first letters of up to two surnames."""
    parts = [name.strip().split()[0]] + surnames.strip().split()[:2]
    return "".join(p[0].upper() for p in parts if p)


class CarFolioService:
    """Service for computing the internal car folio."""

    def __init__(self, car_repository: CarRepository, car_model_repository: CarModelRepository):
        """Initialize with car and car-model repositories."""
        self.car_repo = car_repository
        self.car_model_repo = car_model_repository

    def compute_folio(self, data: CarFolioRequestSchema) -> CarFolioResponseSchema:
        """Compute and return the internal folio for the given inputs."""
        associate = self.car_repo.get_associate_by_id(data.associate_id)
        if not associate:
            raise AssociateNotFoundException(data.associate_id)

        car_model = self.car_model_repo.get_by_make_and_model(data.make, data.model)
        if not car_model:
            raise CarModelNotFoundException(data.make, data.model)

        prefix = _owner_prefix(
            is_us_owner=self.car_repo.is_us_owner(data.associate_id),
            legal_owner_is_pegazzo=data.legal_owner_is_pegazzo,
        )
        initials = _associate_initials(associate.name, associate.surnames)
        consecutive = self.car_repo.count_cars_for_associate(data.associate_id) + 1
        consecutive_str = str(consecutive).zfill(2)

        folio = f"{prefix}-{initials}-{car_model.abbreviation}({data.transmission})-{consecutive_str}"
        return CarFolioResponseSchema(folio=folio)
