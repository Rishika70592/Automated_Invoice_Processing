
import logging
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models import (
    AuditLog,
    Document,
    Invoice,
    ProcessingJob,
    ValidationResult,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------
# Helper: Get current UTC time
# ---------------------------------------------------------

def get_current_time() -> datetime:
    return datetime.now(timezone.utc)


# ---------------------------------------------------------
# Helper: Create audit log
# ---------------------------------------------------------

def create_audit_log(
    db: Session,
    *,
    action: str,
    document_id: str | None = None,
    entity_type: str | None = None,
    entity_id: str | None = None,
    description: str | None = None,
    details: dict | None = None,
) -> AuditLog:

    audit_log = AuditLog(
        document_id=document_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        description=description,
        details=details or {},
    )

    db.add(audit_log)

    return audit_log


# ---------------------------------------------------------
# 1. Start processing job
# ---------------------------------------------------------

def start_processing_job(
    db: Session,
    document_id: str,
) -> ProcessingJob:
    """
    Create and start an invoice processing job.

    Updates the document status and records an audit event.
    """

    try:
        document = db.get(Document, document_id)

        if document is None:
            raise ValueError("Document does not exist.")

        if document.status == "processing":
            raise ValueError(
                "This document is already being processed."
            )

        job = ProcessingJob(
            document_id=document_id,
            job_type="invoice_processing",
            status="processing",
            started_at=get_current_time(),
        )

        document.status = "processing"
        document.extraction_error = None

        db.add(job)
        db.flush()

        create_audit_log(
            db,
            document_id=document_id,
            action="processing_started",
            entity_type="processing_job",
            entity_id=job.id,
            description="Invoice processing started.",
        )

        db.commit()
        db.refresh(job)

        logger.info(
            "Processing job started: %s for document: %s",
            job.id,
            document_id,
        )

        return job

    except Exception:
        db.rollback()
        logger.exception(
            "Failed to start processing job for document %s",
            document_id,
        )
        raise


# ---------------------------------------------------------
# 2. Complete processing job
# ---------------------------------------------------------


def complete_processing_job(
    db: Session,
    job_id: str,
) -> ProcessingJob:
    """
    Complete a processing job after invoice persistence
    and validation have succeeded.
    """

    try:
        job = db.get(ProcessingJob, job_id)

        if job is None:
            raise ValueError(
                "Processing job does not exist."
            )

        if job.status != "processing":
            raise ValueError(
                "Only processing jobs can be completed."
            )

        document = db.get(Document, job.document_id)

        if document is None:
            raise ValueError(
                "Associated document does not exist."
            )

        if document.status != "processing":
            raise ValueError(
                "Document is not in processing state."
            )

        invoice = (
            db.query(Invoice)
            .filter(
                Invoice.document_id == document.id
            )
            .first()
        )

        if invoice is None:
            raise ValueError(
                "Cannot complete processing without an invoice."
            )

        validation_result = (
            db.query(ValidationResult)
            .filter(
                ValidationResult.document_id == document.id,
                ValidationResult.invoice_id == invoice.id,
            )
            .order_by(
                ValidationResult.validated_at.desc()
            )
            .first()
        )

        if validation_result is None:
            raise ValueError(
                "Cannot complete processing without validation."
            )

        # Complete processing job.
        job.status = "completed"
        job.completed_at = get_current_time()

        # Update document and invoice statuses.
        if validation_result.status == "completed":
            document.status = "completed"
            invoice.processing_status = "completed"

        else:
            document.status = "needs_review"
            invoice.processing_status = "needs_review"

        # Record audit event.
        create_audit_log(
            db,
            document_id=document.id,
            action="processing_completed",
            entity_type="processing_job",
            entity_id=job.id,
            description=(
                "Invoice processing completed. "
                f"Validation status: {validation_result.status}."
            ),
            details={
                "invoice_id": invoice.id,
                "validation_status": validation_result.status,
                "document_status": document.status,
                "invoice_status": invoice.processing_status,
            },
        )

        db.commit()
        db.refresh(job)

        logger.info(
            "Processing job completed: %s",
            job.id,
        )

        return job

    except Exception:
        db.rollback()

        logger.exception(
            "Failed to complete processing job %s",
            job_id,
        )

        raise


# ---------------------------------------------------------
# 3. Fail processing job
# ---------------------------------------------------------

def fail_processing_job(
    db: Session,
    job_id: str,
    error_message: str,
) -> ProcessingJob:
    """
    Mark a processing job as failed.

    Updates the associated document and records the failure.
    """

    try:
        if not error_message or not error_message.strip():
            raise ValueError(
                "An error message is required."
            )

        job = db.get(ProcessingJob, job_id)

        if job is None:
            raise ValueError(
                "Processing job does not exist."
            )

        if job.status not in {"processing", "pending"}:
            raise ValueError(
                "Only pending or processing jobs can fail."
            )

        job.status = "failed"
        job.completed_at = get_current_time()
        job.error_message = error_message

        document = db.get(Document, job.document_id)

        if document is not None:
            document.status = "failed"
            document.extraction_error = error_message

            invoice = (
                db.query(Invoice)
                .filter(
                    Invoice.document_id == document.id
                )
                .first()
            )

            if invoice is not None:
                invoice.processing_status = "needs_review"

        create_audit_log(
            db,
            document_id=job.document_id,
            action="processing_failed",
            entity_type="processing_job",
            entity_id=job.id,
            description="Invoice processing failed.",
            details={
                "error": error_message,
            },
        )

        db.commit()
        db.refresh(job)

        logger.error(
            "Processing job failed: %s - %s",
            job.id,
            error_message,
        )

        return job

    except Exception:
        db.rollback()
        logger.exception(
            "Failed to update processing job %s",
            job_id,
        )
        raise


# ---------------------------------------------------------
# 4. Get processing job
# ---------------------------------------------------------

def get_processing_job(
    db: Session,
    job_id: str,
) -> ProcessingJob | None:
    """
    Retrieve a processing job by its ID.
    """

    return db.get(ProcessingJob, job_id)


# ---------------------------------------------------------
# 5. Get document processing jobs
# ---------------------------------------------------------

def get_document_processing_jobs(
    db: Session,
    document_id: str,
) -> list[ProcessingJob]:
    """
    Retrieve all processing jobs associated with a document.
    """

    return (
        db.query(ProcessingJob)
        .filter(
            ProcessingJob.document_id == document_id
        )
        .order_by(
            ProcessingJob.created_at.desc()
        )
        .all()
    )
