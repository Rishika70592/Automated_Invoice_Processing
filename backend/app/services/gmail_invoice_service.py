
import os
import logging
from pathlib import Path

import httpx
from dotenv import load_dotenv

from app.services.gmail_services import fetch_invoice_emails

from app.services.gmail_attachment_service import (
    download_invoice_attachments
)

from app.services.invoice_detection_service import (
    is_invoice,
    InvoiceDetectionError
)


# --------------------------------------------------
# CONFIGURATION
# --------------------------------------------------

load_dotenv()

logger = logging.getLogger(__name__)

UPLOAD_TOKEN = os.getenv("INVOICE_UPLOAD_TOKEN", "").strip()

UPLOAD_URL = os.getenv(
    "INVOICE_UPLOAD_URL",
    "http://127.0.0.1:8000/documents/upload"
).strip().rstrip("/")

EXTRACT_URL = os.getenv(
    "INVOICE_EXTRACT_URL",
    "http://127.0.0.1:8000/documents"
).strip().rstrip("/")

PROCESS_URL = os.getenv(
    "INVOICE_PROCESS_URL",
    "http://127.0.0.1:8000/invoices/process"
).strip().rstrip("/")


# --------------------------------------------------
# HTTP CONFIGURATION
# --------------------------------------------------

TIMEOUT = httpx.Timeout(
    connect=15.0,
    read=180.0,
    write=180.0,
    pool=15.0
)


def get_headers():
    """
    Return optional authentication headers.

    If INVOICE_UPLOAD_TOKEN is empty, no Bearer
    authentication header is sent.
    """

    headers = {}

    if UPLOAD_TOKEN:
        headers["Authorization"] = f"Bearer {UPLOAD_TOKEN}"

    return headers


def validate_configuration():
    """
    Validate required API configuration.
    """

    required_urls = {
        "INVOICE_UPLOAD_URL": UPLOAD_URL,
        "INVOICE_EXTRACT_URL": EXTRACT_URL,
        "INVOICE_PROCESS_URL": PROCESS_URL
    }

    for name, url in required_urls.items():

        if not url:
            raise RuntimeError(
                f"Missing environment variable: {name}"
            )

        if not url.startswith(("http://", "https://")):
            raise RuntimeError(
                f"Invalid URL configured for {name}: {url}"
            )


def cleanup_attachment(attachment):
    """
    Safely remove a downloaded temporary attachment.
    """

    if not attachment:
        return

    file_path = attachment.get("file_path")

    if not file_path:
        return

    try:
        path = Path(file_path)

        if path.is_file():
            path.unlink()

    except OSError:
        logger.exception(
            "Failed to remove temporary attachment: %s",
            file_path
        )


def parse_json_response(response, operation):
    """
    Validate an HTTP response and parse its JSON body.
    """

    if not response.is_success:
        raise RuntimeError(
            f"{operation} failed "
            f"(HTTP {response.status_code}): "
            f"{response.text[:2000]}"
        )

    try:
        data = response.json()

    except ValueError as error:
        raise RuntimeError(
            f"{operation} returned invalid JSON: "
            f"{response.text[:1000]}"
        ) from error

    if not isinstance(data, dict):
        raise RuntimeError(
            f"{operation} returned an unexpected response format."
        )

    return data


# --------------------------------------------------
# PROCESS ONE INVOICE ATTACHMENT
# --------------------------------------------------

def process_invoice_attachment(attachment):
    """
    Upload, extract and process a verified invoice PDF.

    Pipeline:
        1. Upload PDF.
        2. Extract document text.
        3. Process invoice and save structured data.
    """

    validate_configuration()

    file_path = attachment.get("file_path")
    filename = attachment.get("filename", "invoice.pdf")
    mime_type = attachment.get(
        "mime_type",
        "application/pdf"
    )

    if not file_path:
        raise ValueError("Attachment file_path is missing.")

    if not os.path.isfile(file_path):
        raise FileNotFoundError(
            f"Attachment file does not exist: {file_path}"
        )

    headers = get_headers()

    try:

        with httpx.Client(timeout=TIMEOUT) as client:

            # ------------------------------------------
            # STEP 1: UPLOAD DOCUMENT
            # ------------------------------------------

            logger.info("Uploading invoice: %s", filename)

            with open(file_path, "rb") as file:

                upload_response = client.post(
                    UPLOAD_URL,
                    files={
                        "file": (
                            filename,
                            file,
                            mime_type
                        )
                    },
                    headers=headers
                )

            upload_data = parse_json_response(
                upload_response,
                "Document upload"
            )

            document_id = upload_data.get("id")

            if not document_id:
                raise RuntimeError(
                    "Upload response did not contain a document ID."
                )

            logger.info(
                "Document uploaded successfully. ID: %s",
                document_id
            )

            # ------------------------------------------
            # STEP 2: EXTRACT DOCUMENT TEXT
            # ------------------------------------------

            logger.info(
                "Extracting document text: %s",
                document_id
            )

            extraction_url = (
                f"{EXTRACT_URL}/{document_id}/extract"
            )

            extraction_response = client.post(
                extraction_url,
                headers=headers
            )

            extraction_data = parse_json_response(
                extraction_response,
                "Document extraction"
            )

            logger.info(
                "Document extraction completed: %s",
                document_id
            )

            # ------------------------------------------
            # STEP 3: PROCESS INVOICE
            # ------------------------------------------

            logger.info(
                "Processing invoice: %s",
                document_id
            )

            processing_url = (
                f"{PROCESS_URL}/{document_id}"
            )

            processing_response = client.post(
                processing_url,
                headers=headers
            )

            processing_data = parse_json_response(
                processing_response,
                "Invoice processing"
            )

            logger.info(
                "Invoice processing completed: %s",
                document_id
            )

            return {
                "success": True,
                "document_id": document_id,
                "upload": upload_data,
                "extraction": extraction_data,
                "processing": processing_data
            }

    except httpx.TimeoutException as error:

        raise RuntimeError(
            f"API request timed out while processing "
            f"{filename}: {error}"
        ) from error

    except httpx.RequestError as error:

        raise RuntimeError(
            f"Could not connect to the invoice API "
            f"while processing {filename}: {error}"
        ) from error


# --------------------------------------------------
# PROCESS ALL GMAIL INVOICES
# --------------------------------------------------

def process_gmail_invoices(max_results=20):
    """
    Fetch Gmail emails, download attachments, detect invoices,
    and process valid invoice attachments.

    Returns a processing summary.
    """

    if not isinstance(max_results, int) or not 1 <= max_results <= 100:
        raise ValueError(
            "max_results must be an integer between 1 and 100."
        )

    validate_configuration()

    logger.info(
        "Starting Gmail invoice processing. Max results: %s",
        max_results
    )

    # ----------------------------------------------
    # FETCH EMAILS
    # ----------------------------------------------

    emails = fetch_invoice_emails(max_results)

    if not isinstance(emails, list):
        raise RuntimeError(
            "Gmail service returned an unexpected email response."
        )

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

    # ----------------------------------------------
    # PROCESS EACH EMAIL
    # ----------------------------------------------

    for email in emails:

        message_id = email.get("id")

        if not message_id:

            results["failed"] += 1

            results["details"].append({
                "status": "email_processing_failed",
                "error": "Email message ID is missing."
            })

            continue

        attachments = []

        try:

            logger.info(
                "Downloading attachments for email: %s",
                message_id
            )

            attachments = download_invoice_attachments(
                message_id
            )

            if not attachments:

                results["emails_without_attachments"] += 1

                results["details"].append({
                    "message_id": message_id,
                    "status": "no_supported_attachments"
                })

                continue

            results["attachments_found"] += len(attachments)

            # --------------------------------------
            # PROCESS EACH ATTACHMENT
            # --------------------------------------

            for attachment in attachments:

                filename = attachment.get(
                    "filename",
                    "unknown"
                )

                try:

                    file_path = attachment.get("file_path")

                    if not file_path or not os.path.isfile(file_path):
                        raise FileNotFoundError(
                            f"Attachment file is missing: {file_path}"
                        )

                    logger.info(
                        "Checking attachment: %s",
                        filename
                    )

                    # ----------------------------------
                    # STEP 1: DETECT INVOICE
                    # ----------------------------------

                    try:

                        invoice_detected = is_invoice(file_path)

                    except InvoiceDetectionError as error:

                        results["detection_failed"] += 1
                        results["failed"] += 1

                        results["details"].append({
                            "message_id": message_id,
                            "filename": filename,
                            "status": "detection_failed",
                            "error": str(error)
                        })

                        logger.warning(
                            "Invoice detection failed for %s: %s",
                            filename,
                            error
                        )

                        continue

                    # ----------------------------------
                    # STEP 2: SKIP NON-INVOICES
                    # ----------------------------------

                    if not invoice_detected:

                        results["non_invoices_skipped"] += 1

                        results["details"].append({
                            "message_id": message_id,
                            "filename": filename,
                            "status": "skipped_non_invoice"
                        })

                        logger.info(
                            "Skipping non-invoice attachment: %s",
                            filename
                        )

                        continue

                    # ----------------------------------
                    # STEP 3: PROCESS INVOICE
                    # ----------------------------------

                    response = process_invoice_attachment(
                        attachment
                    )

                    results["invoices_processed"] += 1

                    results["details"].append({
                        "message_id": message_id,
                        "filename": filename,
                        "status": "processed",
                        "document_id": response["document_id"]
                    })

                except Exception as error:

                    results["failed"] += 1

                    results["details"].append({
                        "message_id": message_id,
                        "filename": filename,
                        "status": "failed",
                        "error": str(error)
                    })

                    logger.exception(
                        "Failed to process attachment: %s",
                        filename
                    )

                finally:

                    # Always clean up the temporary file.
                    cleanup_attachment(attachment)

        except Exception as error:

            results["failed"] += 1

            results["details"].append({
                "message_id": message_id,
                "status": "email_processing_failed",
                "error": str(error)
            })

            logger.exception(
                "Failed to process Gmail message: %s",
                message_id
            )

            # Clean up any downloaded attachments.
            for attachment in attachments:
                cleanup_attachment(attachment)

    # ----------------------------------------------
    # FINAL SUMMARY
    # ----------------------------------------------

    logger.info(
        "Gmail invoice processing completed. "
        "Emails: %s | Attachments: %s | Processed: %s | "
        "Skipped: %s | Failed: %s",
        results["emails_found"],
        results["attachments_found"],
        results["invoices_processed"],
        results["non_invoices_skipped"],
        results["failed"]
    )

    return results
