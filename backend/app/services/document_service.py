
import hashlib
from uuid import uuid4


def generate_document_id() -> str:
    """Generate a unique UUID for an uploaded document."""
    return str(uuid4())


def calculate_sha256(content: bytes) -> str:
    """Calculate the SHA-256 hexadecimal digest of file contents."""
    return hashlib.sha256(content).hexdigest()
