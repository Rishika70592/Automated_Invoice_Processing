
from pathlib import Path

MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024  # 10 MiB (10,485,760 bytes)

ALLOWED_MIME_TYPES = {
    ".pdf": "application/pdf",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
}


class FileValidationError(ValueError):
    """Raised when an uploaded invoice file fails validation."""


def validate_invoice_file(
    filename: str,
    content: bytes,
    content_type: str | None = None,
) -> str:
    """
    Validate an invoice's filename, size, and basic file signature.

    Returns the normalized file extension when valid.
    Raises FileValidationError when invalid.
    """
    if not filename or not filename.strip():
        raise FileValidationError("A filename is required.")

    # Reject path separators and directory traversal attempts.
    if "/" in filename or "\\" in filename:
        raise FileValidationError("The filename must not contain a path.")

    file_path = Path(filename)
    extension = file_path.suffix.lower()

    if extension not in ALLOWED_MIME_TYPES:
        raise FileValidationError(
            "Unsupported file type. Allowed formats: PDF, JPG, JPEG, PNG."
        )

    if not content:
        raise FileValidationError("The uploaded file is empty.")

    if len(content) > MAX_FILE_SIZE_BYTES:
        raise FileValidationError("File size exceeds the 10 MiB limit.")

    # Check the file signature rather than trusting the extension.
    if extension == ".pdf":
        if not content.startswith(b"%PDF-"):
            raise FileValidationError(
                "The file content does not have a valid PDF signature."
            )

    elif extension in {".jpg", ".jpeg"}:
        if not content.startswith(b"\xff\xd8\xff"):
            raise FileValidationError(
                "The file content does not have a valid JPEG signature."
            )

    elif extension == ".png":
        if not content.startswith(b"\x89PNG\r\n\x1a\n"):
            raise FileValidationError(
                "The file content does not have a valid PNG signature."
            )

    # Reject a declared MIME type that contradicts the filename.
    expected_mime_type = ALLOWED_MIME_TYPES[extension]

    if content_type:
        normalized_content_type = content_type.split(";", 1)[0].strip().lower()

        if normalized_content_type != expected_mime_type:
            raise FileValidationError(
                "The declared content type does not match the file extension."
            )

    return extension
