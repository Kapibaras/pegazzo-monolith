"""Real SQLite session with only the tables of the document analysis flow.

The full schema cannot be created on SQLite (PostgreSQL ARRAY columns), and foreign keys are not enforced, so the
entity tables (car, driver, ...) are not needed for the link rows.
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.models import (
    Document,
    DocumentAnalysis,
    car_document_table,
    driver_document_table,
    garage_document_table,
    guarantor_document_table,
)

ANALYSIS_TABLES = [
    DocumentAnalysis.__table__,
    Document.__table__,
    car_document_table,
    driver_document_table,
    guarantor_document_table,
    garage_document_table,
]


@pytest.fixture
def analysis_db():
    """Yield a SQLite session with the document analysis tables; dropped after the test."""
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    for table in ANALYSIS_TABLES:
        table.create(engine)
    session = sessionmaker(bind=engine, autoflush=False)()
    try:
        yield session
    finally:
        session.close()
        engine.dispose()
