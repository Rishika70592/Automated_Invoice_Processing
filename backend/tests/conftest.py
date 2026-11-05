import os
import pytest

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.database import Base

# Import all models so SQLAlchemy registers their tables
from app.models.document import Document
from app.models.invoice import Invoice
from app.models.supplier import Supplier
from app.models.users import User
from app.models.audit_log import AuditLog
from app.models.processing_job import ProcessingJob
from app.models.invoice_line_item import InvoiceLineItem
from app.models.validation_result import ValidationResult


load_dotenv()

TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL")

if not TEST_DATABASE_URL:
    raise RuntimeError("TEST_DATABASE_URL is missing from .env")


@pytest.fixture(scope="session")
def test_engine():
    engine = create_engine(TEST_DATABASE_URL, pool_pre_ping=True)

    Base.metadata.create_all(bind=engine)

    yield engine

    Base.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest.fixture(scope="function")
def db_session(test_engine):
    TestingSessionLocal = sessionmaker(
        bind=test_engine,
        autoflush=False,
        autocommit=False,
    )

    session = TestingSessionLocal()

    try:
        yield session
    finally:
        session.rollback()
        session.close()