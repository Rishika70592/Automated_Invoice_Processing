
from decimal import Decimal

from app.schemas.invoice import InvoiceData
from app.services.invoice_validation_service import validate_invoice


def test_invalid_total_amount():

    invoice = InvoiceData(
        invoice_number="INV-002",
        supplier_name="ABC Technologies",
        invoice_date="2026-11-10",
        currency="USD",
        subtotal=Decimal("1000.00"),
        tax=Decimal("100.00"),
        discount=Decimal("0.00"),
        total_amount=Decimal("1500.00"),
    )

    result = validate_invoice(invoice)

    assert result["status"] == "needs_review"
    assert result["is_valid"] is False
    assert any(
        error["field"] == "total_amount"
        for error in result["errors"]
    )


def test_missing_required_fields():

    invoice = InvoiceData(
        invoice_number=None,
        supplier_name=None,
        currency=None,
        subtotal=None,
        total_amount=None,
    )

    result = validate_invoice(invoice)

    assert result["status"] == "needs_review"
    assert result["is_valid"] is False
    assert len(result["errors"]) > 0


def test_due_date_before_invoice_date():

    invoice = InvoiceData(
        invoice_number="INV-003",
        supplier_name="ABC Technologies",
        invoice_date="2026-11-20",
        due_date="2026-11-10",
        currency="USD",
        subtotal=Decimal("1000.00"),
        tax=Decimal("100.00"),
        discount=Decimal("0.00"),
        total_amount=Decimal("1100.00"),
    )

    result = validate_invoice(invoice)

    assert result["status"] == "needs_review"
    assert any(
        warning["field"] == "due_date"
        for warning in result["warnings"]
    )

def test_negative_invoice_amount():

    invoice = InvoiceData(
        invoice_number="INV-004",
        supplier_name="ABC Technologies",
        invoice_date="2026-11-10",
        currency="USD",
        subtotal=Decimal("-100.00"),
        tax=Decimal("0.00"),
        discount=Decimal("0.00"),
        total_amount=Decimal("-100.00"),
    )

    result = validate_invoice(invoice)

    assert result["status"] == "needs_review"
    assert any(
        error["field"] == "subtotal"
        for error in result["errors"]
    )


def test_line_item_total_mismatch():

    invoice = InvoiceData(
        invoice_number="INV-005",
        supplier_name="ABC Technologies",
        invoice_date="2026-11-10",
        currency="USD",
        subtotal=Decimal("100.00"),
        tax=Decimal("0.00"),
        discount=Decimal("0.00"),
        total_amount=Decimal("100.00"),
        line_items=[
            {
                "description": "Laptop",
                "quantity": Decimal("2"),
                "unit_price": Decimal("50"),
                "line_total": Decimal("120"),
            }
        ],
    )

    result = validate_invoice(invoice)

    assert result["status"] == "needs_review"
    assert any(
        warning["field"] == "line_items[0].line_total"
        for warning in result["warnings"]
    )
