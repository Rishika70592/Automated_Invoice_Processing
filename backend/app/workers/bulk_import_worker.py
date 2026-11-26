
import logging
import time

from app.db.database import SessionLocal

# Register all SQLAlchemy models.
import app.models  # noqa: F401

from app.services.bulk_import_service import (
    process_one_pending_file,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)

logger = logging.getLogger(__name__)

POLL_INTERVAL_SECONDS = 3

def run_worker():
    logger.info("Bulk import worker started.")

    while True:
        db = SessionLocal()

        try:
            processed = process_one_pending_file(db)

            if not processed:
                time.sleep(POLL_INTERVAL_SECONDS)

        except KeyboardInterrupt:
            logger.info("Bulk import worker stopped.")
            break

        except Exception:
            logger.exception("Bulk import worker error.")
            time.sleep(POLL_INTERVAL_SECONDS)

        finally:
            db.close()

if __name__ == "__main__":
    run_worker()