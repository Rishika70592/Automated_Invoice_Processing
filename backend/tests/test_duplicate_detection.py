
import uuid
from datetime import date
from decimal import Decimal

from app.models.document import Document
from app.models.invoice import Invoice
from app.models.supplier import Supplier

from app.services.duplicate_detection_service import (
    detect_duplicate_invoice,
)


def create_supplier(db, name="ABC Technologies", tax_id=None):
    supplier = Supplier(
        name=name,
        tax_id=tax_id,
    )

    db.add(supplier)
    db.flush()

    return supplier


def create_invoice(
    db,
    supplier,
    invoice_number="INV-001",
    invoice_date=date(2026, 11, 10),
    total_amount=Decimal("1000.00"),
    currency="INR",
):
    unique_id = str(uuid.uuid4())

    document = Document(
        original_filename=f"{unique_id}.pdf",
        stored_filename=f"{unique_id}.pdf",
        storage_path=f"test/{unique_id}.pdf",
        content_type="application/pdf",
        file_size=1000,
        sha256_hash=unique_id.replace("-", "").ljust(64, "0"),
    )

    db.add(document)
    db.flush()

    invoice = Invoice(
        document_id=document.id,
        supplier_id=supplier.id,
        invoice_number=invoice_number,
        invoice_date=invoice_date,
        total_amount=total_amount,
        currency=currency,
    )

    db.add(invoice)
    db.flush()

    return invoice


def test_same_supplier_and_invoice_number(db_session):

    supplier = create_supplier(db_session)

    existing = create_invoice(
        db_session,
        supplier,
        invoice_number="INV-001",
    )

    duplicates = detect_duplicate_invoice(
        db_session,
        supplier_id=supplier.id,
        invoice_number="INV-001",
        invoice_date=date(2026, 11, 10),
        total_amount=Decimal("1000.00"),
        currency="INR",
    )

    assert len(duplicates) == 1
    assert duplicates[0]["invoice_id"] == existing.id
    assert duplicates[0]["match_type"] == "strong"
    assert (
        duplicates[0]["reason"]
        == "same_supplier_and_invoice_number"
    )


def test_same_supplier_date_amount_and_currency(db_session):

    supplier = create_supplier(db_session)

    existing = create_invoice(
        db_session,
        supplier,
        invoice_number="INV-001",
    )

    duplicates = detect_duplicate_invoice(
        db_session,
        supplier_id=supplier.id,
        invoice_number="INV-002",
        invoice_date=date(2026, 11, 10),
        total_amount=Decimal("1000.00"),
        currency="INR",
    )

    assert len(duplicates) == 1
    assert duplicates[0]["invoice_id"] == existing.id
    assert duplicates[0]["match_type"] == "potential"


def test_different_invoice_details_are_not_duplicates(db_session):

    supplier = create_supplier(db_session)

    create_invoice(
        db_session,
        supplier,
        invoice_number="INV-001",
        total_amount=Decimal("1000.00"),
    )

    duplicates = detect_duplicate_invoice(
        db_session,
        supplier_id=supplier.id,
        invoice_number="INV-002",
        invoice_date=date(2026, 11, 11),
        total_amount=Decimal("2000.00"),
        currency="INR",
    )

    assert duplicates == []


def test_different_suppliers_same_invoice_number(db_session):

    supplier1 = create_supplier(
        db_session,
        name="ABC Technologies",
    )

    supplier2 = create_supplier(
        db_session,
        name="XYZ Solutions",
    )

    create_invoice(
        db_session,
        supplier1,
        invoice_number="INV-001",
    )

    duplicates = detect_duplicate_invoice(
        db_session,
        supplier_id=supplier2.id,
        invoice_number="INV-001",
        invoice_date=date(2026, 11, 10),
        total_amount=Decimal("1000.00"),
        currency="INR",
    )

    assert duplicates == []


def test_missing_supplier_id_returns_no_duplicates(db_session):

    duplicates = detect_duplicate_invoice(
        db_session,
        supplier_id=None,
        invoice_number="INV-001",
        invoice_date=date(2026, 11, 10),
        total_amount=Decimal("1000.00"),
        currency="INR",
    )

    assert duplicates == []


def test_exclude_current_invoice(db_session):

    supplier = create_supplier(db_session)

    invoice1 = create_invoice(
        db_session,
        supplier,
        invoice_number="INV-001",
    )

    invoice2 = create_invoice(
        db_session,
        supplier,
        invoice_number="INV-001",
    )

    duplicates = detect_duplicate_invoice(
        db_session,
        supplier_id=supplier.id,
        invoice_number="INV-001",
        invoice_date=date(2026, 11, 10),
        total_amount=Decimal("1000.00"),
        currency="INR",
        exclude_invoice_id=invoice1.id,
    )

    assert len(duplicates) == 1
    assert duplicates[0]["invoice_id"] == invoice2.id
