from app.models.car import Insurance


class InsuranceRepositoryMock:
    """Insurance repository mock class."""

    def __init__(self):
        self.insurances: list[Insurance] = [
            Insurance(id=1, name="AXA Seguros", telephones=["+521234567890"]),
            Insurance(id=2, name="GNP Seguros", telephones=[]),
        ]
        self._next_id = 3
        self.cars_referencing: set[int] = set()

    def reset(self):
        self.insurances = [
            Insurance(id=1, name="AXA Seguros", telephones=["+521234567890"]),
            Insurance(id=2, name="GNP Seguros", telephones=[]),
        ]
        self._next_id = 3
        self.cars_referencing = set()

    def get_by_id(self, insurance_id: int) -> Insurance | None:
        return next((i for i in self.insurances if i.id == insurance_id), None)

    def get_by_name(self, name: str) -> Insurance | None:
        return next((i for i in self.insurances if i.name == name), None)

    def list_all(self, search: str | None = None) -> list[Insurance]:
        if search:
            return [i for i in self.insurances if search.lower() in i.name.lower()]
        return list(self.insurances)

    def is_referenced_by_car(self, insurance_id: int) -> bool:
        return insurance_id in self.cars_referencing

    def create(self, insurance: Insurance) -> Insurance:
        insurance.id = self._next_id
        self._next_id += 1
        self.insurances.append(insurance)
        return insurance

    def update(self, insurance: Insurance) -> Insurance:
        return insurance

    def delete(self, insurance: Insurance) -> None:
        self.insurances = [i for i in self.insurances if i.id != insurance.id]
