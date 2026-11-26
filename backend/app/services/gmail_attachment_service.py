
import base64
import uuid

from pathlib import Path

from app.services.gmail_services import get_gmail_service


BASE_DIR = Path(__file__).resolve().parents[2]
TEMP_DIR = BASE_DIR / "storage" / "gmail_temp"

# Keep this consistent with FastAPI validation_service.py
MAX_FILE_SIZE = 10 * 1024 * 1024

ALLOWED_MIME_TYPES = {
    ".pdf": "application/pdf",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
}


def sanitize_filename(filename):
    """
    Remove directory paths and unsafe filename components.
    Example: taco/invoice.pdf -> invoice.pdf
    """
    filename = str(filename).replace("\\", "/")
    filename = Path(filename).name

    # Remove control characters.
    filename = "".join(
        char for char in filename
        if char.isprintable()
    )

    if not filename or filename in {".", ".."}:
        return None

    if len(filename) > 255:
        extension = Path(filename).suffix
        filename = filename[:255 - len(extension)] + extension

    return filename


def get_message_parts(payload):
    """Recursively retrieve Gmail message parts."""

    parts = []

    if payload.get("filename"):
        parts.append(payload)

    for part in payload.get("parts", []):
        parts.extend(get_message_parts(part))

    return parts


def validate_attachment_signature(extension, file_bytes):
    """Validate actual file signatures."""

    if extension == ".pdf":
        return file_bytes.startswith(b"%PDF-")

    if extension in {".jpg", ".jpeg"}:
        return file_bytes.startswith(b"\xff\xd8\xff")

    if extension == ".png":
        return file_bytes.startswith(
            b"\x89PNG\r\n\x1a\n"
        )

    return False


def download_invoice_attachments(message_id):
    """Download supported Gmail attachments safely."""

    service = get_gmail_service()

    message = service.users().messages().get(
        userId="me",
        id=message_id,
        format="full"
    ).execute()

    payload = message.get("payload", {})
    parts = get_message_parts(payload)

    TEMP_DIR.mkdir(parents=True, exist_ok=True)

    attachments = []

    for part in parts:

        original_filename = part.get("filename", "")

        if not original_filename:
            continue

        # Sanitize filename before passing it to FastAPI.
        filename = sanitize_filename(original_filename)

        if not filename:
            continue

        extension = Path(filename).suffix.lower()

        if extension not in ALLOWED_MIME_TYPES:
            continue

        expected_mime_type = ALLOWED_MIME_TYPES[extension]

        body = part.get("body", {})
        attachment_id = body.get("attachmentId")

        if attachment_id:

            result = service.users().messages().attachments().get(
                userId="me",
                messageId=message_id,
                id=attachment_id
            ).execute()

            encoded_data = result.get("data", "")

        else:
            encoded_data = body.get("data", "")

        if not encoded_data:
            continue

        try:
            # Gmail uses URL-safe Base64.
            encoded_data += "=" * (-len(encoded_data) % 4)

            file_bytes = base64.urlsafe_b64decode(
                encoded_data
            )

        except Exception as error:
            print(
                f"Attachment decoding failed: {filename}: {error}"
            )
            continue

        if not file_bytes:
            continue

        if len(file_bytes) > MAX_FILE_SIZE:
            print(f"Attachment exceeds 10 MiB: {filename}")
            continue

        if not validate_attachment_signature(
            extension,
            file_bytes
        ):
            print(f"Invalid file signature: {filename}")
            continue

        temp_filename = f"{uuid.uuid4()}{extension}"

        file_path = TEMP_DIR / temp_filename

        try:
            file_path.write_bytes(file_bytes)

            attachments.append({
                "filename": filename,
                "original_filename": original_filename,
                "file_path": str(file_path),
                "mime_type": expected_mime_type,
                "file_size": len(file_bytes),
                "message_id": message_id
            })

        except OSError as error:
            print(
                f"Could not save attachment {filename}: {error}"
            )

    return attachments
