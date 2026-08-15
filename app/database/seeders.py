from app.database.session import SessionLocal
from app.enum.auth import Role as RoleEnum
from app.models.car_model import CarModel
from app.models.users import Role

_CAR_MODELS = [
    CarModel(make="BMW", model="X3", abbreviation="BMW"),
    CarModel(make="Ford", model="Focus", abbreviation="FOC"),
    CarModel(make="MG", model="5", abbreviation="MG5"),
    CarModel(make="MG", model="GT", abbreviation="MGGT"),
    CarModel(make="Mazda", model="2", abbreviation="MZ2"),
    CarModel(make="Mazda", model="3", abbreviation="MZ3"),
    CarModel(make="Nissan", model="Magnite", abbreviation="MAG"),
    CarModel(make="Nissan", model="Sentra", abbreviation="SEN"),
    CarModel(make="Nissan", model="V-Drive", abbreviation="VD"),
    CarModel(make="Nissan", model="Versa", abbreviation="VR"),
    CarModel(make="Renault", model="Logan", abbreviation="LOG"),
    CarModel(make="Toyota", model="Avanza", abbreviation="AVZ"),
    CarModel(make="Toyota", model="Prius", abbreviation="PRI"),
    CarModel(make="Toyota", model="Yaris", abbreviation="YR"),
]


def seeders(db: SessionLocal):
    """Seed roles and car model catalog into the database."""
    roles = [
        Role(id=1, name=RoleEnum.OWNER),
        Role(id=2, name=RoleEnum.ADMIN),
        Role(id=3, name=RoleEnum.EMPLOYEE),
    ]

    for role in roles:
        exists = db.query(Role).filter_by(id=role.id).first()
        if not exists:
            db.add(role)
        else:
            exists.name = role.name

    for car_model in _CAR_MODELS:
        exists = db.query(CarModel).filter_by(make=car_model.make, model=car_model.model).first()
        if not exists:
            db.add(car_model)
        else:
            exists.abbreviation = car_model.abbreviation

    db.commit()


if __name__ == "__main__":
    db = SessionLocal()
    seeders(db)
    db.close()
