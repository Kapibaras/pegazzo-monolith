from app.models.car import Associate, Car, Insurance


_DEFAULT_INSURANCE = Insurance(id=1, name="AXA", telephones=["+521234567890"])
_DEFAULT_ASSOCIATE = Associate(id=1, name="Juan", surnames="Pérez", telephones=["+521234567890"])


class CarRepositoryMock:
    """Car repository mock class."""

    def __init__(self):
        self.cars: list[Car] = []
        self.insurances: list[Insurance] = [_DEFAULT_INSURANCE]
        self.associates: list[Associate] = [_DEFAULT_ASSOCIATE]

    def reset(self):
        self.cars = []
        self.insurances = [_DEFAULT_INSURANCE]
        self.associates = [_DEFAULT_ASSOCIATE]

    def get_by_id(self, car_id: str) -> Car | None:
        return next((c for c in self.cars if c.id == car_id), None)

    def get_by_vin(self, vin: str) -> Car | None:
        return next((c for c in self.cars if c.vin == vin), None)

    def get_by_plate(self, plate: str) -> Car | None:
        return next((c for c in self.cars if c.plate == plate), None)

    def get_insurance_by_id(self, insurance_id: int) -> Insurance | None:
        return next((i for i in self.insurances if i.id == insurance_id), None)

    def get_associate_by_id(self, associate_id: int) -> Associate | None:
        return next((a for a in self.associates if a.id == associate_id), None)

    def create_car(self, car: Car, associate: Associate | None) -> Car:
        self.cars.append(car)
        return car
