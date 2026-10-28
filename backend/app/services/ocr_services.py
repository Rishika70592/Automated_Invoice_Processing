
from pathlib import Path

import pymupdf


TESSDATA_DIR = Path(
    r"C:\Program Files\Tesseract-OCR\tessdata"
)

SUPPORTED_IMAGE_EXTENSIONS = {
    ".png", ".jpg", ".jpeg", ".tif", ".tiff", ".bmp"
}


def extract_ocr_text(file_path: str | Path) -> dict:
    """Extract text from scanned PDFs or image invoices using Tesseract."""

    path = Path(file_path)

    if not path.is_file():
        raise FileNotFoundError(f"Document not found: {path.name}")

    extension = path.suffix.lower()

    if extension != ".pdf" and extension not in SUPPORTED_IMAGE_EXTENSIONS:
        raise ValueError("Unsupported OCR document format.")

    if not TESSDATA_DIR.is_dir():
        raise RuntimeError(
            f"Tesseract language data directory not found: {TESSDATA_DIR}"
        )

    pages = []

    with pymupdf.open(str(path)) as document:
        if document.needs_pass:
            raise ValueError("Password-protected PDFs are not supported.")

        if document.page_count == 0:
            raise ValueError("Document contains no pages.")

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
            ).strip()

            pages.append({
                "page_number": page_number,
                "text": text,
                "extraction_method": "ocr",
            })

    return {
        "file_name": path.name,
        "page_count": len(pages),
        "pages": pages,
        "text": "\n\n".join(
            page["text"] for page in pages if page["text"]
        ),
    }
