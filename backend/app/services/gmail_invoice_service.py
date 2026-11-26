
import os
import httpx

from app.services.gmail_services import fetch_invoice_emails

from app.services.gmail_attachment_service import (
    download_invoice_attachments
)

from app.services.invoice_detection_service import (
    is_invoice,
    InvoiceDetectionError
)


UPLOAD_URL = os.getenv(
    "INVOICE_UPLOAD_URL",
    "http://127.0.0.1:8000/documents/upload"
)

EXTRACT_URL = os.getenv(
    "INVOICE_EXTRACT_URL",
    "http://127.0.0.1:8000/documents"
)

UPLOAD_TOKEN = os.getenv("INVOICE_UPLOAD_TOKEN")


def process_invoice_attachment(attachment):
    """Upload and extract a verified invoice."""

    headers = {}

    if UPLOAD_TOKEN:
        headers["Authorization"] = f"Bearer {UPLOAD_TOKEN}"

    with httpx.Client(timeout=180) as client:

        # Step 1: Upload invoice.
        with open(attachment["file_path"], "rb") as file:

            upload_response = client.post(
                UPLOAD_URL,
                files={
                    "file": (
                        attachment["filename"],
                        file,
                        attachment["mime_type"]
                    )
                },
                headers=headers
            )

        if upload_response.status_code != 201:
            raise RuntimeError(
                f"Upload failed "
                f"({upload_response.status_code}): "
                f"{upload_response.text}"
            )

        upload_data = upload_response.json()

        document_id = upload_data["id"]

        # Step 2: Extract invoice text.
        extraction_response = client.post(
            f"{EXTRACT_URL}/{document_id}/extract",
            headers=headers
        )

        if extraction_response.status_code != 200:
            raise RuntimeError(
                f"Extraction failed "
                f"({extraction_response.status_code}): "
                f"{extraction_response.text}"
            )

        return {
            "success": True,
            "document_id": document_id,
            "upload": upload_data,
            "extraction": extraction_response.json()
        }


def process_gmail_invoices(max_results=20):
    """Fetch Gmail attachments and process actual invoices."""

    emails = fetch_invoice_emails(max_results)

    results = {
        "emails_found": len(emails),
        "attachments_found": 0,
        "invoices_processed": 0,
        "non_invoices_skipped": 0,
        "detection_failed": 0,
        "emails_without_attachments": 0,
        "failed": 0,
        "details": []
    }

    for email in emails:

        attachments = []

        try:

            # Step 1: Download supported attachments.
            attachments = download_invoice_attachments(
                email["id"]
            )

            if not attachments:
                results["emails_without_attachments"] += 1

                results["details"].append({
                    "message_id": email["id"],
                    "status": "no_supported_attachments"
                })

                continue

            results["attachments_found"] += len(attachments)

            for attachment in attachments:

                filename = attachment["filename"]
                file_path = attachment["file_path"]

                try:

                    # Step 2: Detect invoice.
                    try:
                        invoice_detected = is_invoice(
                            file_path
                        )

                    except InvoiceDetectionError as error:

                        results["detection_failed"] += 1
                        results["failed"] += 1

                        results["details"].append({
                            "filename": filename,
                            "status": "detection_failed",
                            "error": str(error)
                        })

                        continue

                    # Step 3: Skip non-invoice attachments.
                    if not invoice_detected:

                        results["non_invoices_skipped"] += 1

                        results["details"].append({
                            "filename": filename,
                            "status": "skipped_non_invoice"
                        })

                        continue

                    # Step 4: Upload and extract invoice.
                    response = process_invoice_attachment(
                        attachment
                    )

                    results["invoices_processed"] += 1

                    results["details"].append({
                        "filename": filename,
                        "status": "processed",
                        "document_id": response["document_id"]
                    })

                except Exception as error:

                    results["failed"] += 1

                    results["details"].append({
                        "filename": filename,
                        "status": "failed",
                        "error": str(error)
                    })

                finally:

                    # Always delete temporary files.
                    if os.path.exists(file_path):
                        try:
                            os.remove(file_path)
                        except OSError as error:
                            print(
                                f"Temporary file cleanup failed: "
                                f"{file_path}: {error}"
                            )

        except Exception as error:

            results["failed"] += 1

            results["details"].append({
                "message_id": email["id"],
                "status": "email_processing_failed",
                "error": str(error)
            })

            # Clean up files if email processing fails.
            for attachment in attachments:

                path = attachment["file_path"]

                if os.path.exists(path):
                    try:
                        os.remove(path)
                    except OSError:
                        pass

    return results
