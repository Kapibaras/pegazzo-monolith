from sqlalchemy.orm import joinedload, scoped_session, sessionmaker

from app.database.core import engine
from app.models import Role, User

# Configurar SessionLocal con scoped_session
SessionLocal = scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=engine))


def change_user_role_to_propietario(username: str):
    """Cambia el rol de un usuario a 'propietario'."""
    session = SessionLocal()
    try:
        # Buscar el usuario
        user = session.query(User).filter_by(username=username).first()
        if not user:
            print(f"⚠️ Usuario '{username}' no encontrado.")
            return

        # Buscar el rol propietario
        propietario_role = session.query(Role).filter_by(name="propietario").first()
        if not propietario_role:
            print("⚠️ No existe un rol llamado 'propietario' en la base de datos.")
            return

        # Cambiar el rol
        user.role = propietario_role
        session.commit()

        print(f"✅ Usuario '{username}' ahora tiene el rol 'propietario'.")

    except Exception as e:
        session.rollback()
        print(f"❌ Error al cambiar el rol: {e}")
    finally:
        session.close()


def check_users_and_roles():
    """Obtiene los usuarios con su rol y permisos."""
    session = SessionLocal()
    try:
        users = (
            session.query(User)
            .options(
                joinedload(User.role).joinedload(Role.permissions)  # eager load
            )
            .all()
        )

        if not users:
            print("⚠️ No hay usuarios registrados en la base de datos.")
            return

        for user in users:
            print(f"\n👤 Usuario: {user.username} - {user.name} {user.surnames}")
            print(f"   Rol: {user.role.name}")

            if user.role.permissions:
                print("   Permisos:")
                for perm in user.role.permissions:
                    print(f"     - {perm.name}")
            else:
                print("   (Sin permisos asignados)")

    except Exception as e:
        print(f"❌ Error al obtener usuarios y roles: {e}")
    finally:
        session.close()


if __name__ == "__main__":
    # Cambia aquí el username que quieres actualizar
    change_user_role_to_propietario("JuanOvando")
    check_users_and_roles()
