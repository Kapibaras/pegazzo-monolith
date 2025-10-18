from enum import Enum


class Role(str, Enum):
    """Enum for role names."""

    OWNER = "propietario"
    ADMIN = "administrador"
    EMPLOYEE = "empleado"
