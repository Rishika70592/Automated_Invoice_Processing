
from datetime import date
from decimal import Decimal
import uuid
from unittest.mock import patch
from app.services.invoice_validation_service import validate_invoice
from app.models import (
    Document,
    Invoice,
    Supplier,
)

from app.schemas.invoice import (
    InvoiceData,
    InvoiceExtractionResult,
)

from app.services.invoice_service import (
    process_invoice,
)


def create_document(db):
    unique_id = str(uuid.uuid4())

    document = Document(
        original_filename=f"{unique_id}.pdf",
        stored_filename=f"{unique_id}.pdf",
        storage_path=f"test/{unique_id}.pdf",
        content_type="application/pdf",
        file_size=1000,
        sha256_hash=unique_id.replace("-", "").ljust(64, "0"),
        extracted_text="Invoice Number: INV-001",
        status="uploaded",
    )

    db.add(document)
    db.flush()

    return document


def create_supplier(db):
    supplier = Supplier(
        name="ABC Technologies",
        tax_id="GST12345",
    )

    db.add(supplier)
    db.flush()

    return supplier


def create_existing_invoice(db, supplier):
    document = create_document(db)

    invoice = Invoice(
        document_id=document.id,
        supplier_id=supplier.id,
        invoice_number="INV-001",
        invoice_date=date(2026, 11, 10),
        currency="INR",
        subtotal=Decimal("1000.00"),
        tax=Decimal("100.00"),
        discount=Decimal("0.00"),
        total_amount=Decimal("1100.00"),
        processing_status="completed",
    )

    db.add(invoice)
    db.flush()

    return invoice


def create_extraction_result():
    invoice_data = InvoiceData(
        invoice_number="INV-001",
        supplier_name="ABC Technologies",
        supplier_tax_id="GST12345",
        purchase_order_number=None,
        invoice_date=date(2026, 11, 10),
        due_date=date(2026, 11, 20),
        currency="INR",
        payment_terms="Net 10",
        subtotal=Decimal("1000.00"),
        tax=Decimal("100.00"),
        discount=Decimal("0.00"),
        total_amount=Decimal("1100.00"),
        line_items=[],
        missing_fields=[],
        uncertainty_notes=[],
    )

    return InvoiceExtractionResult(
        data=invoice_data,
        original_text="Invoice Number: INV-001",
        extraction_method="llm",
        model_name="llama3.2:3b",
        confidence=None,
    )


def test_process_duplicate_invoice(db_session):

    # 1. Create existing supplier.
    supplier = create_supplier(db_session)

    # 2. Create an already processed invoice.
    existing_invoice = create_existing_invoice(
        db_session,
        supplier,
    )

    db_session.commit()

    # 3. Create a new document containing the same invoice.
    new_document = create_document(db_session)

    db_session.commit()

    # 4. Mock AI extraction.
    extraction_result = create_extraction_result()

    with patch(
    "app.services.invoice_service.extract_invoice_data",
    return_value=extraction_result,
    ):

        # 5. Process the new document.
        result = process_invoice(
            db=db_session,
            document_id=new_document.id,
        )

    # 6. Verify processing succeeded.
    assert result["success"] is True

    # 7. Verify duplicate detection.
    assert len(result["duplicates"]) == 1

    assert (
        result["duplicates"][0]["invoice_id"]
        == existing_invoice.id
    )

    assert (
        result["duplicates"][0]["match_type"]
        == "strong"
    )

    # 8. Verify validation warning.
    assert result["processing_status"] == "needs_review"

    assert any(
        warning["field"] == "duplicate_invoice"
        for warning in result["validation"]["warnings"]
    )

    # 9. Verify the new invoice was saved.
    new_invoice = db_session.get(
        Invoice,
        result["invoice_id"],
    )

    assert new_invoice is not None
    assert new_invoice.processing_status == "needs_review"

    # 10. Verify document status.
    updated_document = db_session.get(
        Document,
        new_document.id,
    )

    assert updated_document.status == "needs_review"

    # 11. Verify both invoices are preserved.
    invoice_count = (
        db_session.query(Invoice)
        .filter(
            Invoice.supplier_id == supplier.id
        )
        .count()
    )

    assert invoice_count == 2

    # 12. Verify processing job completion.
    from app.models import ProcessingJob

    job = db_session.query(ProcessingJob).filter(
        ProcessingJob.id == result["processing_job_id"]
    ).first()

    assert job is not None
    assert job.status == "completed"
