
import hashlib

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Document


def calculate_file_sha256(file_content: bytes) -> str:
    """Calculate the SHA-256 hash of file content."""
    return hashlib.sha256(file_content).hexdigest()


def find_duplicate_document(
    db: Session,
    *,
    sha256_hash: str,
    exclude_document_id: str | None = None,
) -> Document | None:
    """
    Find an existing document with the same SHA-256 hash.

    Returns the existing Document, or None if no match exists.
    Does not create, update, or delete records.
    """
    query = select(Document).where(
        Document.sha256_hash == sha256_hash
    )

    if exclude_document_id:
        query = query.where(
            Document.id != exclude_document_id
        )

    return db.execute(query).scalars().first()
