
import os
from pathlib import Path

from dotenv import load_dotenv

# Project root: D:\Automated Invoice Process
PROJECT_ROOT = Path(__file__).resolve().parents[2]

# Load environment variables from backend/.env
ENV_FILE = PROJECT_ROOT / ".env"
load_dotenv(ENV_FILE)

# Local directory for original invoice documents.
# Can be overridden later through the INVOICE_STORAGE_DIR environment variable.
_default_storage_dir = PROJECT_ROOT / "storage" / "invoices"

INVOICE_STORAGE_DIR = Path(
    os.getenv("INVOICE_STORAGE_DIR", str(_default_storage_dir))
).expanduser().resolve()


def ensure_storage_directory() -> Path:
    """Create the local invoice storage directory if it doesn't exist."""
    INVOICE_STORAGE_DIR.mkdir(parents=True, exist_ok=True)
    return INVOICE_STORAGE_DIR
