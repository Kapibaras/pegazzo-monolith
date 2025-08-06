from app.database.session import SessionLocal
from app.models.users import Role


def check_roles():
    db = SessionLocal()
    roles = db.query(Role).all()
    db.close()

    print("📋 Roles guardados en la base de datos:")
    for role in roles:
        print(f"🔹 ID: {role.id} | Nombre: {role.name}")


if __name__ == "__main__":
    check_roles()
