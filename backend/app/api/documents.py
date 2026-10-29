
from pathlib import Path
from uuid import uuid4
from datetime import datetime, timezone
from uuid import UUID

from app.config import INVOICE_STORAGE_DIR
from app.services.extraction_service import extract_document_text
from fastapi import APIRouter, File, HTTPException, UploadFile
from sqlalchemy.exc import SQLAlchemyError
from fastapi.responses import FileResponse
from app.db.database import SessionLocal
from app.models.document import Document
from app.services.document_service import (
    calculate_sha256,
    generate_document_id,
)
from app.services.storage_service import delete_document, save_document
from app.services.validation_service import (
    ALLOWED_MIME_TYPES,
    MAX_FILE_SIZE_BYTES,
    FileValidationError,
    validate_invoice_file,
)

router = APIRouter(prefix="/documents", tags=["Documents"])

CHUNK_SIZE = 1024 * 1024  # Read uploads in 1 MiB chunks


@router.post("/upload", status_code=201)
async def upload_document(file: UploadFile = File(...)):
    """Validate an invoice, store its original, and persist its metadata."""

    if not file.filename:
        raise HTTPException(status_code=400, detail="A filename is required.")

    filename = file.filename

    if len(filename) > 255:
        raise HTTPException(
            status_code=400,
            detail="Filename must not exceed 255 characters.",
        )

    # Read incrementally and reject oversized uploads before saving them.
    chunks = []
    total_size = 0

    try:
        while True:
            chunk = await file.read(CHUNK_SIZE)
            if not chunk:
                break

            total_size += len(chunk)

            if total_size > MAX_FILE_SIZE_BYTES:
                raise HTTPException(
                    status_code=413,
                    detail="File size exceeds the 10 MiB limit.",
                )

            chunks.append(chunk)
    finally:
        await file.close()

    content = b"".join(chunks)

    try:
        extension = validate_invoice_file(
            filename=filename,
            content=content,
            content_type=file.content_type,
        )
    except FileValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    document_id = generate_document_id()
    expected_content_type = ALLOWED_MIME_TYPES[extension]

    # Use the generated identifier for the stored filename, never the
    # user-supplied filename.
    try:
        stored_path = save_document(document_id, extension, content)
    except FileExistsError as exc:
        raise HTTPException(
            status_code=409,
            detail="Document identifier conflict. Please retry the upload.",
        ) from exc
    except OSError as exc:
        raise HTTPException(
            status_code=500,
            detail="Could not store the uploaded document.",
        ) from exc

    db = SessionLocal()

    try:
        document = Document(
            id=document_id,
            original_filename=Path(filename).name,
            stored_filename=stored_path.name,
            storage_path=str(stored_path.resolve()),
            content_type=expected_content_type,
            file_size=len(content),
            sha256_hash=calculate_sha256(content),
            status="uploaded",
        )

        db.add(document)
        db.commit()
        db.refresh(document)

        return {
            "id": document.id,
            "original_filename": document.original_filename,
            "stored_filename": document.stored_filename,
            "content_type": document.content_type,
            "file_size": document.file_size,
            "sha256_hash": document.sha256_hash,
            "status": document.status,
            "uploaded_at": document.uploaded_at,
        }

    except SQLAlchemyError as exc:
        db.rollback()

        try:
            delete_document(stored_path)
        except OSError:
            pass

        raise HTTPException(
            status_code=500,
            detail="Could not save document metadata.",
        ) from exc

    finally:
        db.close()

@router.post("/{document_id}/extract")
def extract_document(document_id: str):
    """Extract text from an uploaded document and persist the result."""

    try:
        safe_id = str(UUID(document_id))
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail="Invalid document ID.",
        ) from exc

    db = SessionLocal()

    try:
        document = db.get(Document, safe_id)

        if document is None:
            raise HTTPException(
                status_code=404,
                detail="Document not found.",
            )

        storage_dir = INVOICE_STORAGE_DIR.resolve()
        file_path = Path(document.storage_path).resolve()

        # Ensure the recorded path stays inside the configured storage folder.
        if file_path.parent != storage_dir:
            raise HTTPException(
                status_code=500,
                detail="Stored document path is invalid.",
            )

        if not file_path.is_file():
            raise HTTPException(
                status_code=404,
                detail="Stored document file not found.",
            )

        document.status = "processing"
        document.extraction_error = None
        db.commit()

        try:
            result = extract_document_text(file_path)

            document.extracted_text = result["text"]
            document.extraction_method = result["extraction_method"]
            document.page_count = result["page_count"]
            document.extraction_error = None
            document.extracted_at = datetime.now(timezone.utc)
            document.status = "completed"

            db.commit()
            db.refresh(document)

            return {
                "document_id": document.id,
                "original_filename": document.original_filename,
                "status": document.status,
                "extraction_method": document.extraction_method,
                "page_count": document.page_count,
                "extracted_text": document.extracted_text,
                "extracted_at": document.extracted_at,
            }

        except Exception as exc:
            db.rollback()

            # Reload the document after rollback before recording the failure.
            document = db.get(Document, safe_id)

            if document is not None:
                document.status = "failed"
                document.extraction_error = (
                    f"{type(exc).__name__}: {str(exc)[:1500]}"
                )

                try:
                    db.commit()
                except Exception:
                    db.rollback()
                    raise HTTPException(
                        status_code=500,
                        detail="Extraction failed and its status could not be saved.",
                    ) from exc

            raise HTTPException(
                status_code=422,
                detail="Document extraction failed. Check the document status for details.",
            ) from exc

    finally:
        db.close()


@router.get("/{document_id}/download")
def download_document(document_id: str):
    """Download an uploaded document by its UUID."""

    from uuid import UUID

    from app.config import INVOICE_STORAGE_DIR

    try:
        safe_id = str(UUID(document_id))
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail="Invalid document ID.",
        ) from exc

    db = SessionLocal()

    try:
        document = db.get(Document, safe_id)

        if document is None:
            raise HTTPException(
                status_code=404,
                detail="Document not found.",
            )

        # Resolve the configured storage directory and recorded file path.
        storage_dir = INVOICE_STORAGE_DIR.resolve()
        file_path = Path(document.storage_path).resolve()

        # Refuse paths outside the configured storage directory.
        if file_path.parent != storage_dir:
            raise HTTPException(
                status_code=500,
                detail="Stored document path is invalid.",
            )

        if not file_path.is_file():
            raise HTTPException(
                status_code=404,
                detail="Stored document file not found.",
            )

        return FileResponse(
            path=file_path,
            media_type=document.content_type,
            filename=document.original_filename,
        )

    finally:
        db.close()