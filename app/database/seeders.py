from app.database.session import SessionLocal
from app.models.users import Role


def seed_roles(db: SessionLocal):
    roles = [
        Role(id=1, name="admin"),
        Role(id=2, name="user"),
    ]

    for role in roles:
        exists = db.query(Role).filter_by(id=role.id).first()
        if not exists:
            db.add(role)
        else:
            exists.name = role.name

    db.commit()


if __name__ == "__main__":
    db = SessionLocal()
    seed_roles(db)
    db.close()
