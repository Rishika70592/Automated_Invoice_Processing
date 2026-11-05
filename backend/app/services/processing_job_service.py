from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models import AuditLog, Document, ProcessingJob


def start_processing_job(
    db: Session,
    document_id: str,
) -> ProcessingJob:

    document = db.get(Document, document_id)

    if document is None:
        raise ValueError("Document does not exist.")

    job = ProcessingJob(
        document_id=document_id,
        job_type="invoice_processing",
        status="processing",
        started_at=datetime.now(timezone.utc),
    )

    document.status = "processing"

    db.add(job)
    db.flush()

    db.add(
        AuditLog(
            document_id=document_id,
            action="processing_started",
            entity_type="processing_job",
            entity_id=job.id,
            description="Invoice processing started.",
        )
    )

    db.commit()
    db.refresh(job)

    return job


def complete_processing_job(
    db: Session,
    job_id: str,
) -> ProcessingJob:

    job = db.get(ProcessingJob, job_id)

    if job is None:
        raise ValueError("Processing job does not exist.")

    job.status = "completed"
    job.completed_at = datetime.now(timezone.utc)

    db.add(
        AuditLog(
            document_id=job.document_id,
            action="processing_completed",
            entity_type="processing_job",
            entity_id=job.id,
            description="Invoice processing completed.",
        )
    )

    db.commit()
    db.refresh(job)

    return job


def fail_processing_job(
    db: Session,
    job_id: str,
    error_message: str,
) -> ProcessingJob:

    job = db.get(ProcessingJob, job_id)

    if job is None:
        raise ValueError("Processing job does not exist.")

    job.status = "failed"
    job.completed_at = datetime.now(timezone.utc)
    job.error_message = error_message

    document = db.get(Document, job.document_id)

    if document is not None:
        document.status = "failed"
        document.extraction_error = error_message

    db.add(
        AuditLog(
            document_id=job.document_id,
            action="processing_failed",
            entity_type="processing_job",
            entity_id=job.id,
            description="Invoice processing failed.",
            details={
                "error": error_message,
            },
        )
    )

    db.commit()
    db.refresh(job)

    return job