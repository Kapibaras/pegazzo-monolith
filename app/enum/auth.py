from enum import StrEnum


class Role(StrEnum):
    """Enum for role names."""

    OWNER = "propietario"
    ADMIN = "administrador"
    EMPLOYEE = "empleado"
