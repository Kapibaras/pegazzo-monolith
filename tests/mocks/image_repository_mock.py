from datetime import UTC, datetime

from app.models.car import Car, Insurance
from app.models.driver import Driver

_DEFAULT_INSURANCE = Insurance(id=1, name="AXA", telephones=["+521234567890"])

_DEFAULT_CAR = Car(
    id="CAR001",
    status="active",
    make="Toyota",
    model="Corolla",
    year="2022",
    color="white",
    body_type="sedan",
    engine_type="gasoline",
    transmission="automatic",
    vin="1HGBH41JXMN109186",
    engine_serial_number="ENG001",
    plate="ABC1234",
    odometer=0,
    doors_number=4,
    passengers_number=5,
    unit_value=200000,
    unit_billing_value=200000,
    bill_number="BILL001",
    public_vehicle_registry="REG001",
    tire_specification="195/65R15",
    features={},
    details={},
    legal_owner_name="Pedro",
    legal_owner_surnames="Ramirez",
    battery_model="BAT001",
    battery_serial_number="BATSER001",
    policy_number="POL001",
    insurance_provider_id=1,
    insurance_provider=_DEFAULT_INSURANCE,
    policy_type="full",
    is_financed_liquidated=True,
    agency_image=None,
    photos=[],
    created_at=datetime.now(UTC),
    updated_at=datetime.now(UTC),
)

_DEFAULT_DRIVER = Driver(
    id="DRV001",
    status="active",
    name="Juan",
    surnames="Pérez",
    telephones=["+521234567890"],
    license_number="LIC001",
    identification_number="ID001",
    address="Calle 1",
    garage_address=["Calle 2"],
    photo=None,
    created_at=datetime.now(UTC),
    updated_at=datetime.now(UTC),
)


class ImageRepositoryMock:
    """Mock implementation of ImageRepository for testing purposes."""

    def __init__(self):
        """Initialize the mock with default car and driver entities."""
        self.cars: list[Car] = [_DEFAULT_CAR]
        self.drivers: list[Driver] = [_DEFAULT_DRIVER]

    def reset(self):
        """Reset the mock state to its initial values."""
        self.__init__()

    def get_car_by_id(self, car_id: str) -> Car | None:
        """Return the car with the given ID, or None."""
        return next((c for c in self.cars if c.id == car_id), None)

    def get_driver_by_id(self, driver_id: str) -> Driver | None:
        """Return the driver with the given ID, or None."""
        return next((d for d in self.drivers if d.id == driver_id), None)

    def set_car_agency_image(self, car: Car, url: str) -> Car:
        """Set the agency image URL on the car."""
        car.agency_image = url
        return car

    def add_car_photo(self, car: Car, url: str) -> Car:
        """Append a photo URL to the car's photos list."""
        current = list(car.photos or [])
        current.append(url)
        car.photos = current
        return car

    def remove_car_photo(self, car: Car, url: str) -> Car:
        """Remove a photo URL from the car's photos list."""
        car.photos = [p for p in (car.photos or []) if p != url]
        return car

    def set_driver_photo(self, driver: Driver, url: str) -> Driver:
        """Set the photo URL on the driver."""
        driver.photo = url
        return driver
