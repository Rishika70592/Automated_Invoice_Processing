
import hashlib
import logging
from pathlib import Path
from uuid import uuid4
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models import Document, AuditLog

from app.services.validation_service import (
    validate_invoice_file,
    ALLOWED_MIME_TYPES,
)

from app.services.storage_service import (
    save_document,
    delete_document,
)

from app.services.extraction_service import (
    extract_document_text,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------
# 1. Generate document ID
# ---------------------------------------------------------

def generate_document_id() -> str:
    """Generate a unique UUID for an uploaded document."""
    return str(uuid4())


# ---------------------------------------------------------
# 2. Calculate SHA-256
# ---------------------------------------------------------

def calculate_sha256(content: bytes) -> str:
    """Calculate the SHA-256 hexadecimal digest."""
    return hashlib.sha256(content).hexdigest()


# ---------------------------------------------------------
# 3. Upload and save document
# ---------------------------------------------------------

def upload_document(
    db: Session,
    filename: str,
    content: bytes,
    content_type: str | None = None,
    uploaded_by_user_id: str | None = None,
) -> Document:
    """
    Validate an uploaded invoice and save it to storage.

    Creates a Document database record and an audit log.
    """

    saved_path = None

    try:
        # Validate file.
        extension = validate_invoice_file(
            filename=filename,
            content=content,
            content_type=content_type,
        )

        if len(filename) > 255:
            raise ValueError(
                "Filename exceeds the 255-character limit."
            )

        # Generate identifiers and file metadata.
        document_id = generate_document_id()
        file_hash = calculate_sha256(content)

        expected_content_type = ALLOWED_MIME_TYPES[extension]

        # Save physical file.
        saved_path = save_document(
            document_id=document_id,
            extension=extension,
            content=content,
        )

        # Create database record.
        document = Document(
            id=document_id,
            uploaded_by_user_id=uploaded_by_user_id,
            original_filename=Path(filename).name,
            stored_filename=saved_path.name,
            storage_path=str(saved_path.resolve()),
            content_type=expected_content_type,
            file_size=len(content),
            sha256_hash=file_hash,
            status="uploaded",
        )

        db.add(document)
        db.flush()

        # Record audit event.
        db.add(
            AuditLog(
                user_id=uploaded_by_user_id,
                document_id=document_id,
                action="document_uploaded",
                entity_type="document",
                entity_id=document_id,
                description="Invoice document uploaded successfully.",
                details={
                    "filename": filename,
                    "file_size": len(content),
                    "content_type": expected_content_type,
                    "sha256": file_hash,
                },
            )
        )

        db.commit()
        db.refresh(document)

        logger.info(
            "Document uploaded successfully: %s",
            document_id,
        )

        return document

    except Exception:
        db.rollback()

        # Remove the physical file if database saving fails.
        if saved_path is not None:
            try:
                delete_document(saved_path)
            except OSError:
                logger.exception(
                    "Could not remove uploaded file after database failure."
                )

        logger.exception(
            "Document upload failed: %s",
            filename,
        )

        raise


# ---------------------------------------------------------
# 4. Extract document text
# ---------------------------------------------------------

def extract_and_update_document(
    db: Session,
    document_id: str,
) -> Document:
    """
    Extract text from a stored PDF or image.

    Updates the document's extracted text, page count,
    extraction method and extraction timestamp.
    """

    try:
        document = db.get(Document, document_id)

        if document is None:
            raise ValueError("Document does not exist.")

        file_path = Path(document.storage_path)

        if not file_path.is_file():
            raise FileNotFoundError(
                "Stored invoice document could not be found."
            )

        # Extract PDF or OCR text.
        extraction_result = extract_document_text(file_path)

        extracted_text = extraction_result["text"]

        if not extracted_text.strip():
            raise ValueError(
                "No readable text could be extracted from the document."
            )

        # Update document metadata.
        document.extracted_text = extracted_text

        document.extraction_method = (
            extraction_result["extraction_method"]
        )

        document.page_count = extraction_result["page_count"]

        document.extracted_at = datetime.now(timezone.utc)

        document.extraction_error = None

        db.add(
            AuditLog(
                document_id=document.id,
                action="document_text_extracted",
                entity_type="document",
                entity_id=document.id,
                description="Document text extracted successfully.",
                details={
                    "page_count": document.page_count,
                    "extraction_method": document.extraction_method,
                    "text_length": len(extracted_text),
                },
            )
        )

        db.commit()
        db.refresh(document)

        logger.info(
            "Document text extracted successfully: %s",
            document_id,
        )

        return document

    except Exception as exc:
        db.rollback()

        # Preserve the uploaded document and record extraction failure.
        document = db.get(Document, document_id)

        if document is not None:
            document.extraction_error = str(exc)
            document.status = "failed"

            db.add(
                AuditLog(
                    document_id=document_id,
                    action="document_extraction_failed",
                    entity_type="document",
                    entity_id=document_id,
                    description="Document text extraction failed.",
                    details={
                        "error": str(exc),
                    },
                )
            )

            db.commit()

        logger.exception(
            "Document text extraction failed: %s",
            document_id,
        )

        raise


# ---------------------------------------------------------
# 5. Retrieve document
# ---------------------------------------------------------

def get_document(
    db: Session,
    document_id: str,
) -> Document | None:
    """Retrieve a document using its UUID."""

    return db.get(Document, document_id)


# ---------------------------------------------------------
# 6. Retrieve all documents
# ---------------------------------------------------------

def get_all_documents(
    db: Session,
    limit: int = 100,
    offset: int = 0,
) -> list[Document]:
    """Retrieve documents with pagination."""

    if limit < 1 or limit > 500:
        raise ValueError("Limit must be between 1 and 500.")

    if offset < 0:
        raise ValueError("Offset cannot be negative.")

    return (
        db.query(Document)
        .order_by(Document.uploaded_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )
