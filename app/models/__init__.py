from .balance import Transaction
from .car import Associate, Car, Insurance, associate_car, car_document_table
from .contract import Contract
from .document import Document
from .driver import (
    Driver,
    Guarantor,
    Reference,
    driver_document_table,
    driver_guarantor_table,
    driver_reference_table,
    guarantor_document_table,
    reference_document_table,
)
from .event import Event, Scheduler, event_document_table
from .incidence import Incidence, incidence_document_table
from .users import Permission, Role, User, role_permission_table

__all__ = [
    # Users
    "Role",
    "User",
    "Permission",
    "role_permission_table",
    # Balance
    "Transaction",
    # Car module
    "Car",
    "Insurance",
    "Associate",
    "car_document_table",
    "associate_car",
    # Driver module
    "Driver",
    "Reference",
    "Guarantor",
    "driver_document_table",
    "driver_guarantor_table",
    "driver_reference_table",
    "guarantor_document_table",
    "reference_document_table",
    # Shared
    "Document",
    "Contract",
    # Incidence
    "Incidence",
    "incidence_document_table",
    # Event
    "Event",
    "Scheduler",
    "event_document_table",
]
