
from decimal import Decimal

from app.schemas.invoice import InvoiceData


def validate_invoice(
    invoice: InvoiceData,
) -> dict:
    """
    Validate extracted invoice data using business rules.

    Does not modify the original InvoiceData object.
    """

    errors = []
    warnings = []
    info = []

    # -------------------------------------------------
    # 1. Required field validation
    # -------------------------------------------------

    required_fields = [
        "invoice_number",
        "supplier_name",
        "invoice_date",
        "currency",
        "subtotal",
        "total_amount",
    ]

    for field in required_fields:
        value = getattr(invoice, field)

        if value is None or (
            isinstance(value, str) and not value.strip()
        ):
            errors.append({
                "field": field,
                "message": f"{field} is required.",
                "severity": "error",
            })

    # -------------------------------------------------
    # 2. Currency validation
    # -------------------------------------------------

    if invoice.currency:
        currency = invoice.currency.strip()

        if (
            len(currency) != 3
            or not currency.isalpha()
            or not currency.isascii()
        ):
            errors.append({
                "field": "currency",
                "message": "Currency must be a three-letter code.",
                "severity": "error",
            })

    # -------------------------------------------------
    # 3. Monetary validation
    # -------------------------------------------------

    monetary_fields = {
        "subtotal": invoice.subtotal,
        "tax": invoice.tax,
        "discount": invoice.discount,
        "total_amount": invoice.total_amount,
    }

    for field, value in monetary_fields.items():

        if value is not None:
            if not value.is_finite():
                errors.append({
                    "field": field,
                    "message": "Amount must be a finite number.",
                    "severity": "error",
                })

            elif value < Decimal("0"):
                errors.append({
                    "field": field,
                    "message": "Amount cannot be negative.",
                    "severity": "error",
                })

    # -------------------------------------------------
    # 4. Financial consistency
    # -------------------------------------------------

    if all(
        value is not None
        for value in [
            invoice.subtotal,
            invoice.tax,
            invoice.discount,
            invoice.total_amount,
        ]
    ):
        expected_total = (
            invoice.subtotal
            + invoice.tax
            - invoice.discount
        )

        if abs(
            expected_total - invoice.total_amount
        ) > Decimal("0.02"):

            errors.append({
                "field": "total_amount",
                "message": (
                    f"Expected {expected_total}, "
                    f"but extracted total is "
                    f"{invoice.total_amount}."
                ),
                "severity": "error",
            })

    # -------------------------------------------------
    # 5. Date validation
    # -------------------------------------------------

    if (
        invoice.invoice_date
        and invoice.due_date
        and invoice.due_date < invoice.invoice_date
    ):
        warnings.append({
            "field": "due_date",
            "message": "Due date is earlier than invoice date.",
            "severity": "warning",
        })

    # -------------------------------------------------
    # 6. Line-item validation
    # -------------------------------------------------

    for index, item in enumerate(invoice.line_items):

        prefix = f"line_items[{index}]"

        if item.quantity is not None:
            if (
                not item.quantity.is_finite()
                or item.quantity <= Decimal("0")
            ):
                errors.append({
                    "field": f"{prefix}.quantity",
                    "message": "Quantity must be a positive finite number.",
                    "severity": "error",
                })

        if item.unit_price is not None:
            if (
                not item.unit_price.is_finite()
                or item.unit_price < Decimal("0")
            ):
                errors.append({
                    "field": f"{prefix}.unit_price",
                    "message": "Unit price must be non-negative and finite.",
                    "severity": "error",
                })

        if item.line_total is not None:
            if (
                not item.line_total.is_finite()
                or item.line_total < Decimal("0")
            ):
                errors.append({
                    "field": f"{prefix}.line_total",
                    "message": "Line total must be non-negative and finite.",
                    "severity": "error",
                })

        if (
            item.quantity is not None
            and item.unit_price is not None
            and item.line_total is not None
            and all(
                value.is_finite()
                for value in [
                    item.quantity,
                    item.unit_price,
                    item.line_total,
                ]
            )
            and item.quantity > 0
            and item.unit_price >= 0
            and item.line_total >= 0
        ):
            expected = item.quantity * item.unit_price

            if abs(expected - item.line_total) > Decimal("0.02"):
                warnings.append({
                    "field": f"{prefix}.line_total",
                    "message": (
                        "Line-item total differs from "
                        "quantity multiplied by unit price. "
                        "Check tax and other charges."
                    ),
                    "severity": "warning",
                })

    # -------------------------------------------------
    # 7. Extraction missing fields
    # -------------------------------------------------

    for field in invoice.missing_fields:

        if field not in required_fields:
            info.append({
                "field": field,
                "message": f"Optional or additional field {field} is missing.",
                "severity": "info",
            })

    # -------------------------------------------------
    # 8. Extraction uncertainty
    # -------------------------------------------------

    for note in invoice.uncertainty_notes:
        warnings.append({
            "field": "extraction",
            "message": note,
            "severity": "warning",
        })

    # -------------------------------------------------
    # 9. Final processing status
    # -------------------------------------------------

    
    # -------------------------------------------------
    # 9. Final processing status
    # -------------------------------------------------

    # Warnings are recorded but do not automatically
    # prevent an invoice from being marked completed.
    #
    # Actual validation errors require manual review.

    if errors:
        status = "needs_review"
    else:
        status = "completed"

    return {
        "status": status,
        "is_valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
        "info": info,
    }

