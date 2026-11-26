
import logging
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models import (
    ImportBatch,
    ImportBatchFile,
    Invoice,
)

from app.services.document_service import (
    extract_and_update_document,
)

from app.services.invoice_service import process_invoice


logger = logging.getLogger(__name__)


def get_current_time():
    return datetime.now(timezone.utc)


# ---------------------------------------------------------
# 1. Update batch status
# ---------------------------------------------------------

def update_batch_status(
    db: Session,
    batch_id: str,
):
    """
    Recalculate batch progress and update its overall status.
    """

    batch = db.get(ImportBatch, batch_id)

    if batch is None:
        return

    files = (
        db.query(ImportBatchFile)
        .filter(
            ImportBatchFile.batch_id == batch_id
        )
        .all()
    )

    total = len(files)

    completed = sum(
        item.status == "completed"
        for item in files
    )

    failed = sum(
        item.status == "failed"
        for item in files
    )

    pending = sum(
        item.status == "pending"
        for item in files
    )

    processing = sum(
        item.status == "processing"
        for item in files
    )

    batch.total_files = total
    batch.completed_files = completed
    batch.failed_files = failed

    # Batch is still running.
    if pending > 0 or processing > 0:
        batch.status = "processing"
        batch.completed_at = None

    # All files have finished.
    elif total > 0:
        batch.status = "completed"
        batch.completed_at = get_current_time()

    else:
        batch.status = "failed"
        batch.completed_at = get_current_time()

    db.commit()

    logger.info(
        "Batch %s updated: total=%s completed=%s failed=%s",
        batch_id,
        total,
        completed,
        failed,
    )


# ---------------------------------------------------------
# 2. Process one batch file
# ---------------------------------------------------------

def process_batch_file(
    db: Session,
    batch_file_id: str,
):
    """
    Extract and process one invoice document.

    Uses the existing document extraction service
    and existing invoice processing service.
    """

    item = db.get(
        ImportBatchFile,
        batch_file_id,
    )

    if item is None:
        raise ValueError(
            "Batch file does not exist."
        )

    if item.status != "pending":
        logger.warning(
            "Skipping batch file %s because its status is %s",
            batch_file_id,
            item.status,
        )
        return

    batch_id = item.batch_id
    document_id = item.document_id

    # Mark file as processing.
    item.status = "processing"
    item.started_at = get_current_time()
    item.error_message = None

    db.commit()

    try:

        # -------------------------------------------------
        # STEP 1: Extract PDF or OCR text
        # -------------------------------------------------

        document = extract_and_update_document(
            db=db,
            document_id=document_id,
        )

        if document is None:
            raise ValueError(
                "Document could not be retrieved."
            )

        if not document.extracted_text:
            raise ValueError(
                "No readable text was extracted from the document."
            )

        # -------------------------------------------------
        # STEP 2: Process invoice using existing AI service
        # -------------------------------------------------

        process_invoice(
            db=db,
            document_id=document_id,
        )

        # -------------------------------------------------
        # STEP 3: Retrieve saved invoice from database
        # -------------------------------------------------

        invoice = (
            db.query(Invoice)
            .filter(
                Invoice.document_id == document_id
            )
            .first()
        )

        if invoice is None:
            raise ValueError(
                "Invoice processing finished, but no invoice "
                "record was found for this document."
            )

        # -------------------------------------------------
        # STEP 4: Mark batch file completed
        # -------------------------------------------------

        item = db.get(
            ImportBatchFile,
            batch_file_id,
        )

        if item is None:
            raise ValueError(
                "Batch file disappeared during processing."
            )

        item.status = "completed"
        item.invoice_id = str(invoice.id)
        item.error_message = None
        item.completed_at = get_current_time()

        db.commit()

        logger.info(
            "Invoice successfully processed: %s",
            item.filename,
        )

    except Exception as exc:

        logger.exception(
            "Failed to process batch file %s",
            batch_file_id,
        )

        db.rollback()

        # Record this file's failure without stopping
        # the remaining files in the batch.
        item = db.get(
            ImportBatchFile,
            batch_file_id,
        )

        if item is not None:

            item.status = "failed"
            item.error_message = str(exc)[:5000]
            item.completed_at = get_current_time()

            db.commit()

    finally:

        # Recalculate batch progress.
        update_batch_status(
            db=db,
            batch_id=batch_id,
        )


# ---------------------------------------------------------
# 3. Process the next pending file
# ---------------------------------------------------------

def process_one_pending_file(
    db: Session,
) -> bool:
    """
    Find and process the oldest pending file.

    This implementation assumes only one worker process
    is running.
    """

    item = (
        db.query(ImportBatchFile)
        .filter(
            ImportBatchFile.status == "pending"
        )
        .order_by(
            ImportBatchFile.created_at.asc()
        )
        .first()
    )

    if item is None:
        return False

    logger.info(
        "Starting bulk import file: %s",
        item.filename,
    )

    process_batch_file(
        db=db,
        batch_file_id=item.id,
    )

    return True
