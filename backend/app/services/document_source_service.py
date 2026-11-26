
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models import Document, DocumentSource


VALID_SOURCE_TYPES = {
    "manual_upload",
    "gmail",
    "microsoft_graph",
    "s3",
    "bulk_import",
}

VALID_SOURCE_STATUSES = {
    "received",
    "registered",
    "processing",
    "completed",
    "failed",
    "duplicate",
}


def get_source(
    db: Session,
    source_type: str,
    source_reference: str,
):
    statement = select(DocumentSource).where(
        DocumentSource.source_type == source_type,
        DocumentSource.source_reference == source_reference,
    )
    return db.execute(statement).scalar_one_or_none()


def register_document_source(
    db: Session,
    *,
    document_id: str,
    source_type: str,
    source_reference: str,
    file_hash: str | None = None,
    source_metadata: dict | None = None,
    status: str = "registered",
):
    if source_type not in VALID_SOURCE_TYPES:
        raise ValueError("Unsupported source type.")

    if status not in VALID_SOURCE_STATUSES:
        raise ValueError("Unsupported source status.")

    if not source_reference or len(source_reference) > 1000:
        raise ValueError("Invalid source reference.")

    document = db.get(Document, document_id)

    if document is None:
        raise ValueError("Document does not exist.")

    existing = get_source(
        db,
        source_type,
        source_reference,
    )

    if existing:
        return existing, False

    source = DocumentSource(
        document_id=document_id,
        source_type=source_type,
        source_reference=source_reference,
        file_hash=file_hash,
        source_metadata=source_metadata,
        status=status,
    )

    db.add(source)

    try:
        db.commit()
        db.refresh(source)
        return source, True

    except IntegrityError:
        db.rollback()

        # Another request may have registered this source
        # at almost exactly the same time.
        existing = get_source(
            db,
            source_type,
            source_reference,
        )

        if existing:
            return existing, False

        raise


def update_source_status(
    db: Session,
    source_id: str,
    status: str,
    error_message: str | None = None,
):
    if status not in VALID_SOURCE_STATUSES:
        raise ValueError("Unsupported source status.")

    source = db.get(DocumentSource, source_id)

    if source is None:
        raise ValueError("Document source not found.")

    source.status = status
    source.error_message = error_message
    source.updated_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(source)

    return source
