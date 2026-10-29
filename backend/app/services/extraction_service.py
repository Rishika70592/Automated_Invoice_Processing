
import re
from pathlib import Path

import pymupdf

from app.services.ocr_services import (
    SUPPORTED_IMAGE_EXTENSIONS,
    TESSDATA_DIR,
)
from app.services.pdf_extractor import extract_pdf_text


MIN_EMBEDDED_TEXT_LENGTH = 30


def normalize_text(text: str) -> str:
    """Normalize whitespace while preserving meaningful line breaks."""
    lines = [re.sub(r"[ \t]+", " ", line).strip() for line in text.splitlines()]
    lines = [line for line in lines if line]
    return "\n".join(lines)


def extract_document_text(file_path: str | Path) -> dict:
    """
    Extract text from digital PDFs, scanned PDFs, and supported images.

    Digital PDF pages use embedded text when sufficient.
    OCR is applied only to PDF pages with insufficient embedded text.
    """
    path = Path(file_path)

    if not path.is_file():
        raise FileNotFoundError("Document file not found.")

    extension = path.suffix.lower()

    if extension == ".pdf":
        result = extract_pdf_text(path)
        pages = []

        with pymupdf.open(str(path)) as document:
            for page_info, page in zip(result["pages"], document):
                text = page_info["text"]
                method = "pdf_text"

                if len(text.strip()) < MIN_EMBEDDED_TEXT_LENGTH:
                    if not TESSDATA_DIR.is_dir():
                        raise RuntimeError(
                            "Tesseract language data directory was not found."
                        )

                    text_page = page.get_textpage_ocr(
                        language="eng",
                        dpi=200,
                        full=True,
                        tessdata=str(TESSDATA_DIR),
                    )
                    text = page.get_text(
                        textpage=text_page,
                        sort=True,
                    )
                    method = "ocr"

                pages.append({
                    "page_number": page_info["page_number"],
                    "text": normalize_text(text),
                    "extraction_method": method,
                })

        methods = {page["extraction_method"] for page in pages}

        if methods == {"pdf_text"}:
            overall_method = "pdf_text"
        elif methods == {"ocr"}:
            overall_method = "ocr"
        else:
            overall_method = "mixed"

    elif extension in SUPPORTED_IMAGE_EXTENSIONS:
        if not TESSDATA_DIR.is_dir():
            raise RuntimeError(
                "Tesseract language data directory was not found."
            )

        pages = []

        with pymupdf.open(str(path)) as document:
            for page_number, page in enumerate(document, start=1):
                text_page = page.get_textpage_ocr(
                    language="eng",
                    dpi=200,
                    full=True,
                    tessdata=str(TESSDATA_DIR),
                )
                text = page.get_text(
                    textpage=text_page,
                    sort=True,
                )

                pages.append({
                    "page_number": page_number,
                    "text": normalize_text(text),
                    "extraction_method": "ocr",
                })

        overall_method = "ocr"

    else:
        raise ValueError("Unsupported document format.")

    combined_text = "\n\n".join(
        page["text"] for page in pages if page["text"]
    )

    return {
        "file_name": path.name,
        "page_count": len(pages),
        "pages": pages,
        "text": combined_text,
        "extraction_method": overall_method,
    }
