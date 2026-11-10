
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import Invoice, Supplier


def detect_duplicate_invoice(
    db: Session,
    *,
    supplier_id: str | None,
    invoice_number: str | None,
    invoice_date,
    total_amount,
    currency: str | None,
    exclude_invoice_id: str | None = None,
) -> list[dict]:
    """
    Detect potential duplicate invoices.

    Does not create, update, or delete database records.
    """

    if not supplier_id:
        return []

    query = (
        select(Invoice, Supplier.name)
        .join(
            Supplier,
            Invoice.supplier_id == Supplier.id,
        )
        .where(
            Invoice.supplier_id == supplier_id,
        )
    )

    if exclude_invoice_id:
        query = query.where(
            Invoice.id != exclude_invoice_id
        )

    existing_invoices = db.execute(query).all()

    duplicates = []

    normalized_number = (
        invoice_number.strip().casefold()
        if invoice_number
        else None
    )

    normalized_currency = (
        currency.strip().upper()
        if currency
        else None
    )

    for existing_invoice, supplier_name in existing_invoices:

        existing_number = (
            existing_invoice.invoice_number.strip().casefold()
            if existing_invoice.invoice_number
            else None
        )

        existing_currency = (
            existing_invoice.currency.strip().upper()
            if existing_invoice.currency
            else None
        )

        # Rule 1: Same supplier and invoice number.
        if (
            normalized_number
            and existing_number
            and normalized_number == existing_number
        ):
            duplicates.append({
                "invoice_id": existing_invoice.id,
                "invoice_number": existing_invoice.invoice_number,
                "supplier_name": supplier_name,
                "reason": "same_supplier_and_invoice_number",
                "match_type": "strong",
            })

            continue

        # Rule 2: Same supplier, date, amount and currency.
        if (
            invoice_date is not None
            and total_amount is not None
            and normalized_currency is not None
            and existing_invoice.invoice_date == invoice_date
            and existing_invoice.total_amount == total_amount
            and existing_currency == normalized_currency
        ):
            duplicates.append({
                "invoice_id": existing_invoice.id,
                "invoice_number": existing_invoice.invoice_number,
                "supplier_name": supplier_name,
                "reason": "same_supplier_date_amount_currency",
                "match_type": "potential",
            })

    return duplicates
