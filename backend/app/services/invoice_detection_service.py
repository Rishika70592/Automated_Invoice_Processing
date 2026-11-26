
import pymupdf
import pytesseract

from PIL import Image


INVOICE_IDENTIFIERS = [
    "invoice",
    "tax invoice",
    "invoice number",
    "invoice no",
    "bill number",
    "bill no",
]

FINANCIAL_INDICATORS = [
    "total amount",
    "amount due",
    "subtotal",
    "grand total",
    "tax amount",
    "gst",
    "vat",
    "balance due",
    "total",
]

PARTY_INDICATORS = [
    "supplier",
    "vendor",
    "bill to",
    "sold to",
    "customer",
    "seller",
    "billed to",
]


class InvoiceDetectionError(Exception):
    """Raised when invoice detection cannot be completed."""


def looks_like_invoice(text):
    """Determine whether extracted text resembles an invoice."""

    text = " ".join(text.lower().split())

    if not text:
        return False

    has_identifier = any(
        keyword in text
        for keyword in INVOICE_IDENTIFIERS
    )

    has_financial = any(
        keyword in text
        for keyword in FINANCIAL_INDICATORS
    )

    has_party = any(
        keyword in text
        for keyword in PARTY_INDICATORS
    )

    # An invoice identifier and financial information
    # are the minimum required indicators.
    if has_identifier and has_financial:
        return True

    # Alternative combination for invoices where the
    # document heading is not clearly extracted.
    if has_financial and has_party:
        return (
            "invoice" in text
            or "bill" in text
        )

    return False


def extract_pdf_text(file_path):
    """Extract PDF text, using OCR for scanned pages."""

    document = None

    try:
        document = pymupdf.open(file_path)

        if document.is_encrypted:
            raise InvoiceDetectionError(
                "Encrypted PDF cannot be inspected."
            )

        if len(document) == 0:
            raise InvoiceDetectionError(
                "PDF contains no pages."
            )

        extracted_text = []

        for page in document:

            page_text = page.get_text()

            # Use OCR for scanned PDF pages.
            if len(page_text.strip()) < 30:

                pix = page.get_pixmap(
                    matrix=pymupdf.Matrix(2, 2),
                    alpha=False
                )

                image = Image.frombytes(
                    "RGB",
                    [pix.width, pix.height],
                    pix.samples
                )

                ocr_text = pytesseract.image_to_string(
                    image
                )

                page_text += "\n" + ocr_text

            extracted_text.append(page_text)

        return "\n".join(extracted_text)

    except InvoiceDetectionError:
        raise

    except Exception as error:
        raise InvoiceDetectionError(
            f"PDF text extraction failed: {error}"
        ) from error

    finally:
        if document is not None:
            document.close()


def extract_image_text(file_path):
    """Extract text from an image using OCR."""

    try:
        with Image.open(file_path) as image:
            image = image.convert("RGB")

            return pytesseract.image_to_string(image)

    except Exception as error:
        raise InvoiceDetectionError(
            f"Image text extraction failed: {error}"
        ) from error


def is_invoice(file_path):
    """Check whether the document is an invoice."""

    file_path = str(file_path)

    extension = file_path.lower().rsplit(".", 1)[-1]

    try:

        if extension == "pdf":
            text = extract_pdf_text(file_path)

        elif extension in {"jpg", "jpeg", "png"}:
            text = extract_image_text(file_path)

        else:
            raise InvoiceDetectionError(
                "Unsupported document format."
            )

        if not text or not text.strip():
            raise InvoiceDetectionError(
                "No readable text found in document."
            )

        return looks_like_invoice(text)

    except InvoiceDetectionError:
        raise

    except Exception as error:
        raise InvoiceDetectionError(
            f"Invoice detection failed: {error}"
        ) from error
