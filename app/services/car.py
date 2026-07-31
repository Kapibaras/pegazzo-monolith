import math
from datetime import UTC, datetime, timedelta

from app.errors.car import (
    AssociateNotFoundException,
    CarIdAlreadyExistsException,
    CarNotFoundException,
    CarPlateAlreadyExistsException,
    CarVinAlreadyExistsException,
    InsuranceProviderNotFoundException,
    PolicyExpirationDateInPastException,
)
from app.models.car import Car
from app.repositories.car import CarRepository
from app.schemas.car import (
    AssignedDriverSchema,
    AssociateDetailSchema,
    CarDetailResponseSchema,
    CarListQuerySchema,
    CarListResponseSchema,
    CarSchema,
    DocumentDetailSchema,
    InsuranceDetailSchema,
    PaginationSchema,
)
from app.storage import r2

_EXPIRING_SOON_DAYS = 30


def _compute_expiry_status(expiry_date) -> str | None:
    """Return valid / expiring_soon / expired based on expiry_date, or None if no expiry."""
    if expiry_date is None:
        return None
    now = datetime.now(UTC)
    if now > expiry_date:
        return "expired"
    if now + timedelta(days=_EXPIRING_SOON_DAYS) > expiry_date:
        return "expiring_soon"
    return "valid"


class CarService:
    """Car service class."""

    def __init__(self, repository: CarRepository):
        """Initialize the car service with a repository."""
        self.repository = repository

    def get_car(self, car_id: str) -> CarDetailResponseSchema:
        """Return the full detail for a single car, or raise 404 if not found."""
        car = self.repository.get_by_id(car_id)
        if not car:
            raise CarNotFoundException(car_id)

        documents = [
            DocumentDetailSchema(
                id=doc.id,
                type=doc.type,
                category=doc.category,
                expiry_date=doc.expiry_date,
                url=r2.generate_document_read_url(doc.url),
                expiry_status=_compute_expiry_status(doc.expiry_date),
            )
            for doc in self.repository.get_car_documents(car_id)
        ]

        contract = self.repository.get_active_contract_for_car(car_id)
        assigned_driver = None
        if contract and contract.driver:
            assigned_driver = AssignedDriverSchema(
                id=contract.driver.id,
                name=contract.driver.name,
                surnames=contract.driver.surnames,
            )

        associate = None
        if car.associate:
            a = car.associate[0]
            associate = AssociateDetailSchema(
                id=a.id,
                name=a.name,
                surnames=a.surnames,
                telephones=a.telephones,
            )

        ins = car.insurance_provider
        insurance = InsuranceDetailSchema(
            id=ins.id,
            name=ins.name,
            policy_number=car.policy_number,
            policy_expiration_date=car.policy_expiration_date,
            policy_type=car.policy_type,
        )

        return CarDetailResponseSchema(
            id=car.id,
            make=car.make,
            model=car.model,
            year=car.year,
            color=car.color,
            status=car.status,
            vin=car.vin,
            plate=car.plate,
            body_type=car.body_type,
            engine_type=car.engine_type,
            transmission=car.transmission,
            engine_serial_number=car.engine_serial_number,
            odometer=car.odometer,
            doors_number=car.doors_number,
            passengers_number=car.passengers_number,
            tire_specification=car.tire_specification,
            unit_value=float(car.unit_value),
            unit_billing_value=float(car.unit_billing_value),
            bill_number=car.bill_number,
            public_vehicle_registry=car.public_vehicle_registry,
            alta_public_vehicle_registry=car.alta_public_vehicle_registry,
            battery_model=car.battery_model,
            battery_serial_number=car.battery_serial_number,
            battery_date=car.battery_date,
            legal_owner_name=car.legal_owner_name,
            legal_owner_surnames=car.legal_owner_surnames,
            financed_status=car.financed_status,
            features=car.features,
            details=car.details,
            agency_image=car.agency_image,
            photos=car.photos,
            archived_at=car.archived_at,
            created_at=car.created_at,
            updated_at=car.updated_at,
            insurance=insurance,
            associate=associate,
            documents=documents,
            assigned_driver=assigned_driver,
        )

    def list_cars(self, params: CarListQuerySchema) -> CarListResponseSchema:
        """Return a paginated, filtered and sorted list of cars."""
        offset = (params.page - 1) * params.limit
        total = self.repository.count_cars(status=params.status, search=params.search, archived=params.archived)
        cars = self.repository.list_cars(
            status=params.status,
            search=params.search,
            archived=params.archived,
            sort_by=params.sort_by,
            sort_order=params.sort_order,
            limit=params.limit,
            offset=offset,
        )
        return CarListResponseSchema(
            cars=cars,
            pagination=PaginationSchema(
                page=params.page,
                limit=params.limit,
                total=total,
                total_pages=0 if total == 0 else math.ceil(total / params.limit),
            ),
        )

    def create_car(self, data: CarSchema) -> Car:
        """Create a new car with validations."""
        if self.repository.get_by_id(data.id):
            raise CarIdAlreadyExistsException(data.id)

        if self.repository.get_by_vin(data.vin):
            raise CarVinAlreadyExistsException(data.vin)

        if self.repository.get_by_plate(data.plate):
            raise CarPlateAlreadyExistsException(data.plate)

        now_utc = datetime.now(UTC)
        if data.policy_expiration_date <= now_utc:
            raise PolicyExpirationDateInPastException

        if not self.repository.get_insurance_by_id(data.insurance_provider_id):
            raise InsuranceProviderNotFoundException(data.insurance_provider_id)

        associate = None
        if data.associate_id is not None:
            associate = self.repository.get_associate_by_id(data.associate_id)
            if not associate:
                raise AssociateNotFoundException(data.associate_id)

        car = Car(
            id=data.id,
            make=data.make,
            model=data.model,
            year=data.year,
            color=data.color,
            status=data.status,
            vin=data.vin,
            plate=data.plate,
            body_type=data.body_type,
            engine_type=data.engine_type,
            transmission=data.transmission,
            engine_serial_number=data.engine_serial_number,
            odometer=data.odometer,
            doors_number=data.doors_number,
            passengers_number=data.passengers_number,
            tire_specification=data.tire_specification,
            unit_value=data.unit_value,
            unit_billing_value=data.unit_billing_value,
            bill_number=data.bill_number,
            public_vehicle_registry=data.public_vehicle_registry,
            alta_public_vehicle_registry=data.alta_public_vehicle_registry,
            battery_model=data.battery_model,
            battery_serial_number=data.battery_serial_number,
            battery_date=data.battery_date,
            legal_owner_name=data.legal_owner_name,
            legal_owner_surnames=data.legal_owner_surnames,
            financed_status=data.financed_status,
            features=data.features,
            details=data.details,
            insurance_provider_id=data.insurance_provider_id,
            policy_number=data.policy_number,
            policy_expiration_date=data.policy_expiration_date,
            policy_type=data.policy_type,
        )

        return self.repository.create_car(car, associate)
