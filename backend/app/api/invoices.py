from datetime import date
from uuid import UUID
from app.schemas.invoice import InvoiceData
from app.services.invoice_validation_service import validate_invoice
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, selectinload

from app.db.database import get_db
from app.models import (
    Document,
    Invoice,
    InvoiceLineItem,
    Supplier,
    ValidationResult,
)
from app.schemas.invoice_management import (
    InvoiceUpdate,
)

from app.services.invoice_service import process_invoice


router = APIRouter(
    prefix="/invoices",
    tags=["Invoices"],
)


# ---------------------------------------------------------
# Helper: Validate UUID
# ---------------------------------------------------------

def validate_uuid(value: str) -> str:
    try:
        return str(UUID(value))
    except (ValueError, TypeError, AttributeError):
        raise HTTPException(
            status_code=400,
            detail="Invalid UUID.",
        )


# ---------------------------------------------------------
# 1. Process Uploaded Invoice
# ---------------------------------------------------------

@router.post("/process/{document_id}")
def process_uploaded_invoice(
    document_id: str,
    db: Session = Depends(get_db),
):
    document_id = validate_uuid(document_id)

    document = db.get(Document, document_id)

    if document is None:
        raise HTTPException(
            status_code=404,
            detail="Document not found.",
        )

    try:
        result = process_invoice(
            db=db,
            document_id=document_id,
        )

        return result

    except ValueError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail="Invoice processing failed.",
        ) from exc


# ---------------------------------------------------------
# 2. List Invoices
# ---------------------------------------------------------

@router.get("")
def list_invoices(
    search: str | None = None,
    status: str | None = None,
    supplier_id: str | None = None,
    currency: str | None = None,
    start_date: date | None = None,
    end_date: date | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    query = (
        select(Invoice)
        .options(
            selectinload(Invoice.supplier),
            selectinload(Invoice.line_items),
        )
    )

    # Search by invoice number or supplier name.
    if search:
        search_term = f"%{search.strip()}%"

        query = query.join(
            Supplier,
            Invoice.supplier_id == Supplier.id,
            isouter=True,
        ).where(
            or_(
                Invoice.invoice_number.ilike(search_term),
                Supplier.name.ilike(search_term),
            )
        )

    # Filter by processing status.
    if status:
        query = query.where(
            Invoice.processing_status == status
        )

    # Filter by supplier.
    if supplier_id:
        supplier_id = validate_uuid(supplier_id)

        query = query.where(
            Invoice.supplier_id == supplier_id
        )

    # Filter by currency.
    if currency:
        query = query.where(
            Invoice.currency == currency.upper()
        )

    # Filter by invoice date.
    if start_date:
        query = query.where(
            Invoice.invoice_date >= start_date
        )

    if end_date:
        query = query.where(
            Invoice.invoice_date <= end_date
        )

    if start_date and end_date and start_date > end_date:
        raise HTTPException(
            status_code=400,
            detail="Start date cannot be after end date.",
        )

    # Count matching invoices before pagination.
    count_query = select(func.count()).select_from(
        query.order_by(None).subquery()
    )

    total = db.scalar(count_query) or 0

    # Pagination.
    query = (
        query
        .order_by(Invoice.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )

    invoices = db.scalars(query).all()

    results = []

    for invoice in invoices:
        results.append(
            {
                "id": invoice.id,
                "document_id": invoice.document_id,
                "invoice_number": invoice.invoice_number,
                "supplier": (
                    invoice.supplier.name
                    if invoice.supplier
                    else None
                ),
                "supplier_id": invoice.supplier_id,
                "invoice_date": invoice.invoice_date,
                "due_date": invoice.due_date,
                "currency": invoice.currency,
                "subtotal": invoice.subtotal,
                "tax": invoice.tax,
                "discount": invoice.discount,
                "total_amount": invoice.total_amount,
                "processing_status": invoice.processing_status,
                "line_item_count": len(invoice.line_items),
                "created_at": invoice.created_at,
            }
        )

    return {
        "success": True,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (
            (total + page_size - 1) // page_size
        ),
        "invoices": results,
    }


# ---------------------------------------------------------
# 3. Get Invoice Details
# ---------------------------------------------------------

@router.get("/{invoice_id}")
def get_invoice(
    invoice_id: str,
    db: Session = Depends(get_db),
):
    invoice_id = validate_uuid(invoice_id)

    invoice = db.scalar(
        select(Invoice)
        .options(
            selectinload(Invoice.supplier),
            selectinload(Invoice.line_items),
            selectinload(Invoice.document),
        )
        .where(Invoice.id == invoice_id)
    )

    if invoice is None:
        raise HTTPException(
            status_code=404,
            detail="Invoice not found.",
        )

    return {
        "success": True,
        "invoice": {
            "id": invoice.id,
            "document_id": invoice.document_id,
            "invoice_number": invoice.invoice_number,
            "purchase_order_number": invoice.purchase_order_number,
            "supplier_id": invoice.supplier_id,
            "supplier": (
                {
                    "id": invoice.supplier.id,
                    "name": invoice.supplier.name,
                    "tax_id": invoice.supplier.tax_id,
                }
                if invoice.supplier
                else None
            ),
            "invoice_date": invoice.invoice_date,
            "due_date": invoice.due_date,
            "currency": invoice.currency,
            "payment_terms": invoice.payment_terms,
            "subtotal": invoice.subtotal,
            "tax": invoice.tax,
            "discount": invoice.discount,
            "total_amount": invoice.total_amount,
            "processing_status": invoice.processing_status,
            "extraction_method": invoice.extraction_method,
            "model_name": invoice.model_name,
            "line_items": [
                {
                    "id": item.id,
                    "description": item.description,
                    "quantity": item.quantity,
                    "unit_price": item.unit_price,
                    "tax_rate": item.tax_rate,
                    "tax_amount": item.tax_amount,
                    "line_total": item.line_total,
                }
                for item in invoice.line_items
            ],
            "document": (
                {
                    "original_filename": invoice.document.original_filename,
                    "content_type": invoice.document.content_type,
                    "file_size": invoice.document.file_size,
                    "status": invoice.document.status,
                }
                if invoice.document
                else None
            ),
            "created_at": invoice.created_at,
            "updated_at": invoice.updated_at,
        },
    }


# ---------------------------------------------------------
# 4. Update Invoice
# ---------------------------------------------------------


@router.put("/{invoice_id}")
def update_invoice(
    invoice_id: str,
    payload: InvoiceUpdate,
    db: Session = Depends(get_db),
):
    invoice_id = validate_uuid(invoice_id)

    invoice = db.scalar(
        select(Invoice)
        .options(selectinload(Invoice.line_items))
        .where(Invoice.id == invoice_id)
    )

    if invoice is None:
        raise HTTPException(
            status_code=404,
            detail="Invoice not found.",
        )

    update_data = payload.model_dump(exclude_unset=True)

    line_items = update_data.pop("line_items", None)

    # Preserve existing values for fields not submitted.
    for field, value in update_data.items():
        setattr(invoice, field, value)

    # Replace line items only when explicitly provided.
    if line_items is not None:
        invoice.line_items.clear()

        for item in line_items:
            invoice.line_items.append(
                InvoiceLineItem(**item)
            )

    try:
        # Rebuild structured invoice data.
        invoice_data = InvoiceData(
            invoice_number=invoice.invoice_number,
            supplier_name=(
                invoice.supplier.name
                if invoice.supplier
                else None
            ),
            purchase_order_number=invoice.purchase_order_number,
            invoice_date=invoice.invoice_date,
            due_date=invoice.due_date,
            currency=invoice.currency,
            payment_terms=invoice.payment_terms,
            subtotal=invoice.subtotal,
            tax=invoice.tax,
            discount=invoice.discount,
            total_amount=invoice.total_amount,
            line_items=[
                {
                    "description": item.description,
                    "quantity": item.quantity,
                    "unit_price": item.unit_price,
                    "tax_rate": item.tax_rate,
                    "tax_amount": item.tax_amount,
                    "line_total": item.line_total,
                }
                for item in invoice.line_items
            ],
        )

        # Run validation again.
        validation = validate_invoice(invoice_data)

        invoice.processing_status = validation["status"]

        # Store a new validation history record.
        db.add(
            ValidationResult(
                document_id=invoice.document_id,
                invoice_id=invoice.id,
                status=validation["status"],
                errors=validation["errors"],
                warnings=validation["warnings"],
                info=validation["info"],
                notes="Invoice revalidated after manual correction.",
            )
        )

        db.commit()
        db.refresh(invoice)

        return {
            "success": True,
            "message": "Invoice updated and revalidated successfully.",
            "invoice_id": invoice.id,
            "processing_status": invoice.processing_status,
            "validation": validation,
        }

    except Exception as exc:
        db.rollback()

        if isinstance(exc, HTTPException):
            raise

        raise HTTPException(
            status_code=500,
            detail="Could not update and validate invoice.",
        ) from exc


# ---------------------------------------------------------
# 5. Get Invoice Validation History
# ---------------------------------------------------------

@router.get("/{invoice_id}/validation")
def get_invoice_validation(
    invoice_id: str,
    db: Session = Depends(get_db),
):
    invoice_id = validate_uuid(invoice_id)

    invoice = db.get(
        Invoice,
        invoice_id,
    )

    if invoice is None:
        raise HTTPException(
            status_code=404,
            detail="Invoice not found.",
        )

    validation_results = db.scalars(
        select(ValidationResult)
        .where(
            ValidationResult.invoice_id == invoice_id
        )
        .order_by(
            ValidationResult.validated_at.desc()
        )
    ).all()

    return {
        "success": True,
        "invoice_id": invoice_id,
        "current_status": invoice.processing_status,
        "validation_history": [
            {
                "id": result.id,
                "status": result.status,
                "errors": result.errors,
                "warnings": result.warnings,
                "info": result.info,
                "notes": result.notes,
                "validated_at": result.validated_at,
            }
            for result in validation_results
        ],
    }