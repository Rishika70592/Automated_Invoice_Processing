
from pathlib import Path
from uuid import UUID

from app.config import INVOICE_STORAGE_DIR, ensure_storage_directory


def save_document(document_id: str, extension: str, content: bytes) -> Path:
    """
    Save document bytes under a generated UUID filename.

    The caller is responsible for validating the document before saving it.
    A partial file is removed if writing fails.
    """
    # Ensure the identifier is a valid UUID and normalize the extension.
    safe_id = str(UUID(document_id))
    safe_extension = extension.lower()

    if safe_extension not in {".pdf", ".jpg", ".jpeg", ".png"}:
        raise ValueError("Unsupported storage file extension.")

    storage_dir = ensure_storage_directory()
    destination = storage_dir / f"{safe_id}{safe_extension}"

    # Never overwrite an existing document.
    if destination.exists():
        raise FileExistsError("A document with this identifier already exists.")

    try:
        with destination.open("xb") as file:
            file.write(content)
    except Exception:
        # Remove a partial file if the write failed.
        try:
            destination.unlink(missing_ok=True)
        except OSError:
            pass
        raise

    return destination


def delete_document(path: str | Path) -> None:
    """
    Delete a document only when it is directly inside the configured
    invoice storage directory.
    """
    storage_dir = INVOICE_STORAGE_DIR.resolve()
    candidate = Path(path).resolve()

    if candidate.parent != storage_dir:
        raise ValueError("Refusing to delete a file outside invoice storage.")

    candidate.unlink(missing_ok=True)
