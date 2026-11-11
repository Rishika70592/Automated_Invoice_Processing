
import io
import uuid
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.db.database import get_db
from app.models import Document, Invoice, Supplier
from app.schemas.invoice import (
    InvoiceData,
    InvoiceExtractionResult,
)
from tests.conftest import db_session


@pytest.fixture
def client(db_session):
    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


def create_test_pdf():
    """
    Create a minimal valid PDF for upload testing.
    Uses a mocked extractor, so actual PDF text is not required.
    """
    from reportlab.pdfgen import canvas

    buffer = io.BytesIO()
    pdf = canvas.Canvas(buffer)
    pdf.drawString(100, 750, "Invoice Number: INT-001")
    pdf.drawString(100, 730, "Supplier: ABC Technologies")
    pdf.drawString(100, 710, "Total: 1100.00")
    pdf.save()

    buffer.seek(0)
    return buffer


def create_extraction_result():
    return InvoiceExtractionResult(
        data=InvoiceData(
            invoice_number="INT-001",
            supplier_name="ABC Technologies",
            supplier_tax_id="INT-GST-001",
            invoice_date="2026-11-10",
            due_date="2026-11-20",
            currency="INR",
            subtotal="1000.00",
            tax="100.00",
            discount="0.00",
            total_amount="1100.00",
            line_items=[],
        ),
        original_text=(
            "Invoice Number: INT-001\n"
            "Supplier: ABC Technologies\n"
            "Total: 1100.00"
        ),
        extraction_method="llm",
        model_name="test-model",
    )


def test_health_endpoint(client):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_complete_invoice_workflow(client, db_session):

    # 1. Upload invoice PDF.
    pdf = create_test_pdf()

    upload_response = client.post(
        "/documents/upload",
        files={
            "file": (
                "integration_invoice.pdf",
                pdf,
                "application/pdf",
            )
        },
    )

    assert upload_response.status_code == 201

    document_id = upload_response.json()["id"]

    # 2. Mock document text extraction.
    with patch(
        "app.api.documents.extract_document_text",
        return_value={
            "text": (
                "Invoice Number: INT-001\n"
                "Supplier: ABC Technologies\n"
                "Total: 1100.00"
            ),
            "extraction_method": "pdfplumber",
            "page_count": 1,
        },
    ):

        extraction_response = client.post(
            f"/documents/{document_id}/extract"
        )

    assert extraction_response.status_code == 200
    assert extraction_response.json()["status"] == "completed"

    # 3. Mock invoice extraction.
    with patch(
        "app.services.invoice_service.extract_invoice_data",
        return_value=create_extraction_result(),
    ):

        processing_response = client.post(
            f"/invoices/process/{document_id}"
        )

    assert processing_response.status_code == 200

    processing_data = processing_response.json()

    assert processing_data["success"] is True

    invoice_id = processing_data["invoice_id"]

    # 4. Verify invoice listing.
    list_response = client.get("/invoices")

    assert list_response.status_code == 200

    invoice_ids = [
        item["id"]
        for item in list_response.json()["invoices"]
    ]

    assert invoice_id in invoice_ids

    # 5. Verify invoice details.
    detail_response = client.get(
        f"/invoices/{invoice_id}"
    )

    assert detail_response.status_code == 200

    invoice_data = detail_response.json()["invoice"]

    assert invoice_data["invoice_number"] == "INT-001"
    assert invoice_data["currency"] == "INR"

    # 6. Verify validation history.
    validation_response = client.get(
        f"/invoices/{invoice_id}/validation"
    )

    assert validation_response.status_code == 200

    assert len(
        validation_response.json()["validation_history"]
    ) >= 1

    # 7. Verify document and invoice persistence.
    document = db_session.get(Document, document_id)
    invoice = db_session.get(Invoice, invoice_id)

    assert document is not None
    assert invoice is not None
    assert document.invoice.id == invoice.id


def test_invalid_document_id(client):

    response = client.post(
        "/documents/invalid-id/extract"
    )

    assert response.status_code == 400


def test_nonexistent_invoice(client):

    response = client.get(
        f"/invoices/{uuid.uuid4()}"
    )

    assert response.status_code == 404


def test_nonexistent_document_processing(client):

    response = client.post(
        f"/invoices/process/{uuid.uuid4()}"
    )

    assert response.status_code == 404
