
import logging

from sqlalchemy import select, func
from sqlalchemy.orm import Session

from app.models import (
    Document,
    Invoice,
    Supplier,
)

from app.services.invoice_persistence_service import (
    persist_invoice,
)

from app.services.invoice_extractor_service import (
    extract_invoice_data,
)

from app.services.invoice_validation_service import (
    validate_invoice,
)

from app.services.processing_job_service import (
    start_processing_job,
    complete_processing_job,
    fail_processing_job,
)

from app.services.duplicate_detection_service import (
    detect_duplicate_invoice,
)


logger = logging.getLogger(__name__)


def process_invoice(
    db: Session,
    document_id: str,
    model_name: str | None = None,
) -> dict:

    job = None

    try:
        # 1. Retrieve document.
        document = db.get(Document, document_id)

        if document is None:
            raise ValueError("Document does not exist.")

        if not document.extracted_text or not document.extracted_text.strip():
            raise ValueError(
                "Document does not contain extracted text."
            )

        # 2. Prevent duplicate invoice creation for the same document.
        existing_invoice = (
            db.query(Invoice)
            .filter(Invoice.document_id == document_id)
            .first()
        )

        if existing_invoice is not None:
            raise ValueError(
                "An invoice has already been created for this document."
            )

        # 3. Start processing job.
        job = start_processing_job(
            db=db,
            document_id=document_id,
        )

        # 4. Extract invoice data.
        extraction_result = extract_invoice_data(
            document.extracted_text,
            model_name=model_name,
        )

        extracted_data = extraction_result.data

        # 5. Validate invoice.
        validation = validate_invoice(extracted_data)

        # 6. Find existing supplier.
        supplier = None

        if extracted_data.supplier_tax_id:
            supplier = db.scalar(
               select(Supplier).where(
                  Supplier.tax_id == extracted_data.supplier_tax_id.strip()
        )
    )

        if supplier is None and extracted_data.supplier_name:
            supplier = db.scalar(
               select(Supplier).where(
                  func.lower(Supplier.name)
                  == extracted_data.supplier_name.strip().lower()
        )
    )

        # 7. Detect potential duplicate invoices.
        duplicates = detect_duplicate_invoice(
            db=db,
            supplier_id=supplier.id if supplier else None,
            invoice_number=extracted_data.invoice_number,
            invoice_date=extracted_data.invoice_date,
            total_amount=extracted_data.total_amount,
            currency=extracted_data.currency,
        )

        if duplicates:
            validation["warnings"].append({
                "field": "duplicate_invoice",
                "message": "Potential duplicate invoice detected.",
                "severity": "warning",
                "matches": duplicates,
            })

            validation["status"] = "needs_review"

        # 8. Persist invoice and validation results.
        invoice = persist_invoice(
            db=db,
            document_id=document_id,
            extraction_result=extraction_result,
            validation=validation,
        )

        # 9. Commit persistence transaction.
        db.commit()
        db.refresh(invoice)

        # 10. Complete processing job.
        completed_job = complete_processing_job(
            db=db,
            job_id=job.id,
        )

        logger.info(
            "Invoice processing completed: %s",
            document_id,
        )

        return {
            "success": True,
            "document_id": document_id,
            "invoice_id": invoice.id,
            "processing_job_id": completed_job.id,
            "processing_status": invoice.processing_status,
            "validation": validation,
            "duplicates": duplicates,
            "invoice": extracted_data.model_dump(mode="json"),
        }

    except Exception as exc:

        db.rollback()

        logger.exception(
            "Invoice processing failed: %s",
            document_id,
        )

        if job is not None:
            try:
                fail_processing_job(
                    db=db,
                    job_id=job.id,
                    error_message=str(exc),
                )

            except Exception:
                db.rollback()

                logger.exception(
                    "Could not mark processing job as failed."
                )

        raise
