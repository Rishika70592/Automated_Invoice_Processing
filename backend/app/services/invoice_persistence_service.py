import logging
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models import (
    AuditLog,
    Document,
    Invoice,
    InvoiceLineItem,
    Supplier,
)
from app.schemas.invoice import InvoiceExtractionResult

logger = logging.getLogger(__name__)


class InvoicePersistenceError(Exception):
    """Raised when invoice persistence fails."""


def persist_invoice(
    db: Session,
    document_id: str,
    extraction_result: InvoiceExtractionResult,
) -> Invoice:

    try:
        document = db.get(Document, document_id)

        if document is None:
            raise InvoicePersistenceError(
                f"Document {document_id} does not exist."
            )

        data = extraction_result.data

        # 1. Find or create supplier.
        supplier = None

        if data.supplier_name:
            if data.supplier_tax_id:
                supplier = db.scalar(
                    select(Supplier).where(
                        Supplier.tax_id == data.supplier_tax_id
                    )
                )

            if supplier is None:
                supplier = db.scalar(
                    select(Supplier).where(
                        Supplier.name == data.supplier_name
                    )
                )

            if supplier is None:
                supplier = Supplier(
                    name=data.supplier_name,
                    tax_id=data.supplier_tax_id,
                )
                db.add(supplier)
                db.flush()

        # 2. Find an existing invoice for this document.
        invoice = db.scalar(
            select(Invoice)
            .options(selectinload(Invoice.line_items))
            .where(Invoice.document_id == document_id)
        )

        if invoice is None:
            invoice = Invoice(
                document_id=document_id,
            )
            db.add(invoice)
            db.flush()
        else:
            # Replace previous extracted line items.
            invoice.line_items.clear()

        # 3. Save invoice-level information.
        invoice.supplier_id = supplier.id if supplier else None
        invoice.invoice_number = data.invoice_number
        invoice.purchase_order_number = data.purchase_order_number
        invoice.invoice_date = data.invoice_date
        invoice.due_date = data.due_date
        invoice.currency = data.currency
        invoice.payment_terms = data.payment_terms
        invoice.subtotal = data.subtotal
        invoice.tax = data.tax
        invoice.discount = data.discount
        invoice.total_amount = data.total_amount

        invoice.extraction_method = extraction_result.extraction_method
        invoice.model_name = extraction_result.model_name

        # 4. Save every line item.
        for item in data.line_items:
            line_item = InvoiceLineItem(
                description=item.description,
                quantity=item.quantity,
                unit_price=item.unit_price,
                tax_rate=item.tax_rate,
                tax_amount=item.tax_amount,
                line_total=item.line_total,
            )

            invoice.line_items.append(line_item)

        # 5. Update document status.
        document.status = "extracted"
        document.extraction_method = extraction_result.extraction_method
        document.extracted_at = datetime.now(timezone.utc)

        # 6. Record audit activity.
        db.add(
            AuditLog(
                document_id=document.id,
                action="invoice_extracted",
                entity_type="invoice",
                entity_id=invoice.id,
                description="Invoice extraction persisted successfully.",
                details={
                    "invoice_number": data.invoice_number,
                    "supplier_name": data.supplier_name,
                    "line_item_count": len(data.line_items),
                    "model_name": extraction_result.model_name,
                },
            )
        )

        # 7. Commit transaction.
        db.commit()

        db.refresh(invoice)

        logger.info(
            "Invoice persisted successfully. Invoice ID: %s",
            invoice.id,
        )

        return invoice

    except Exception as exc:
        db.rollback()

        logger.exception(
            "Invoice persistence failed for document %s.",
            document_id,
        )

        if isinstance(exc, InvoicePersistenceError):
            raise

        raise InvoicePersistenceError(
            "Could not persist invoice data."
        ) from exc