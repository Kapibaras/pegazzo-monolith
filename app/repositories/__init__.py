from .associate import AssociateRepository
from .balance import BalanceRepository
from .car import CarRepository
from .car_model import CarModelRepository
from .document import DocumentRepository
from .driver import DriverRepository
from .garage import GarageRepository
from .guarantor import GuarantorRepository
from .image import ImageRepository
from .insurance import InsuranceRepository
from .user import UserRepository

__all__ = [
    "AssociateRepository",
    "BalanceRepository",
    "CarModelRepository",
    "CarRepository",
    "DocumentRepository",
    "DriverRepository",
    "GarageRepository",
    "GuarantorRepository",
    "ImageRepository",
    "InsuranceRepository",
    "UserRepository",
]
