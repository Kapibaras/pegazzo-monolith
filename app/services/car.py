from datetime import datetime, timezone

from app.errors.car import (
    AssociateNotFoundException,
    CarIdAlreadyExistsException,
    CarPlateAlreadyExistsException,
    CarVinAlreadyExistsException,
    InsuranceProviderNotFoundException,
    PolicyExpirationDateInPastException,
)
from app.models.car import Car
from app.repositories.car import CarRepository
from app.schemas.car import CarSchema


class CarService:
    """Car service class."""

    def __init__(self, repository: CarRepository):
        self.repository = repository

    def create_car(self, data: CarSchema) -> Car:
        """Create a new car with validations."""
        if self.repository.get_by_id(data.id):
            raise CarIdAlreadyExistsException(data.id)

        if self.repository.get_by_vin(data.vin):
            raise CarVinAlreadyExistsException(data.vin)

        if self.repository.get_by_plate(data.plate):
            raise CarPlateAlreadyExistsException(data.plate)

        now_utc = datetime.now(timezone.utc)
        if data.policy_expiration_date <= now_utc:
            raise PolicyExpirationDateInPastException()

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
