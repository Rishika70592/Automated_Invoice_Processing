
from uuid import UUID

from fastapi import (
    APIRouter,
    Depends,
    File,
    HTTPException,
    UploadFile,
)
from sqlalchemy.orm import Session

from app.db.database import get_db

from app.models import ImportBatch, ImportBatchFile

from app.services.document_service import upload_document

from app.services.validation_service import MAX_FILE_SIZE_BYTES

router = APIRouter(
    prefix="/bulk-import",
    tags=["Bulk Import"],
)

MAX_FILES_PER_BATCH = 10

@router.post("/upload")
async def upload_bulk_invoices(
    files: list[UploadFile] = File(...),
    db: Session = Depends(get_db),
):
    """
    Upload up to 10 invoice files and create a batch.

    Files are saved individually using the existing
    document upload service.
    """

    if not files:
        raise HTTPException(
            status_code=400,
            detail="Please select at least one file.",
        )

    if len(files) > MAX_FILES_PER_BATCH:
        raise HTTPException(
            status_code=400,
            detail=f"You can upload a maximum of {MAX_FILES_PER_BATCH} files.",
        )

    batch = ImportBatch(
        status="pending",
        total_files=0,
        completed_files=0,
        failed_files=0,
    )

    db.add(batch)
    db.commit()
    db.refresh(batch)

    uploaded_files = []
    rejected_files = []

    for file in files:
        try:
            if not file.filename:
                raise ValueError("Filename is missing.")

            # Read at most one byte above the allowed limit.
            content = await file.read(MAX_FILE_SIZE_BYTES + 1)

            if len(content) > MAX_FILE_SIZE_BYTES:
                raise ValueError("File size must not exceed 10 MB.")

            # Reuse existing validation, storage, DB and audit logic.
            document = upload_document(
                db=db,
                filename=file.filename,
                content=content,
                content_type=file.content_type,
            )

            batch_file = ImportBatchFile(
                batch_id=batch.id,
                document_id=document.id,
                filename=document.original_filename,
                status="pending",
            )

            db.add(batch_file)
            db.commit()
            db.refresh(batch_file)

            uploaded_files.append({
                "document_id": document.id,
                "batch_file_id": batch_file.id,
                "filename": batch_file.filename,
                "status": batch_file.status,
            })

        except Exception as exc:
            db.rollback()

            rejected_files.append({
                "filename": file.filename or "unknown",
                "error": str(exc),
            })

        finally:
            await file.close()

    if not uploaded_files:
        batch.status = "failed"
        batch.total_files = 0
        db.commit()

        raise HTTPException(
            status_code=400,
            detail={
                "message": "No files could be uploaded.",
                "rejected_files": rejected_files,
            },
        )

    batch.total_files = len(uploaded_files)
    batch.status = "pending"

    db.commit()

    return {
        "message": "Bulk invoice upload completed.",
        "batch_id": batch.id,
        "total_files": batch.total_files,
        "uploaded_files": uploaded_files,
        "rejected_files": rejected_files,
        "status": batch.status,
    }

@router.get("/{batch_id}")
def get_bulk_import_status(
    batch_id: str,
    db: Session = Depends(get_db),
):
    """Return the current progress of a bulk import."""

    try:
        UUID(batch_id)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="Invalid batch ID.",
        )

    batch = db.get(ImportBatch, batch_id)

    if batch is None:
        raise HTTPException(
            status_code=404,
            detail="Bulk import batch not found.",
        )

    batch_files = (
        db.query(ImportBatchFile)
        .filter(ImportBatchFile.batch_id == batch_id)
        .order_by(ImportBatchFile.created_at.asc())
        .all()
    )

    pending = sum(
        item.status == "pending" for item in batch_files
    )

    processing = sum(
        item.status == "processing" for item in batch_files
    )

    return {
        "batch_id": batch.id,
        "status": batch.status,
        "total_files": batch.total_files,
        "completed_files": batch.completed_files,
        "failed_files": batch.failed_files,
        "pending_files": pending,
        "processing_files": processing,
        "progress_percentage": (
            round(
                (
                    batch.completed_files + batch.failed_files
                ) / batch.total_files * 100,
                2,
            )
            if batch.total_files
            else 0
        ),
        "files": [
            {
                "id": item.id,
                "document_id": item.document_id,
                "filename": item.filename,
                "status": item.status,
                "invoice_id": item.invoice_id,
                "error_message": item.error_message,
                "started_at": (
                    item.started_at.isoformat()
                    if item.started_at else None
                ),
                "completed_at": (
                    item.completed_at.isoformat()
                    if item.completed_at else None
                ),
            }
            for item in batch_files
        ],
    }