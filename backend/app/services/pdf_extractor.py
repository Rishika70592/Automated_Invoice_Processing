from pathlib import Path

import pymupdf


def extract_pdf_text(file_path: str | Path) -> dict:
    """Extract embedded text from a digital PDF, page by page."""

    path = Path(file_path)

    if not path.is_file():
        raise FileNotFoundError(f"Document not found: {path.name}")

    if path.suffix.lower() != ".pdf":
        raise ValueError("This extractor accepts PDF files only.")

    pages = []

    with pymupdf.open(str(path)) as document:
        if document.needs_pass:
            raise ValueError("Password-protected PDFs are not supported.")

        if document.page_count == 0:
            raise ValueError("The PDF contains no pages.")

        for page_number, page in enumerate(document, start=1):
            text = page.get_text("text", sort=True).strip()

            pages.append({
                "page_number": page_number,
                "text": text,
                "extraction_method": "pdf_text",
                "needs_ocr": len(text) < 30,
            })

    return {
        "file_name": path.name,
        "page_count": len(pages),
        "pages": pages,
        "text": "\n\n".join(
            page["text"] for page in pages if page["text"]
        ),
        "needs_ocr": any(page["needs_ocr"] for page in pages),
    }