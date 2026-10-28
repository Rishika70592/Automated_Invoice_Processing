from pathlib import Path

from app.services.pdf_extractor import extract_pdf_text
from app.services.ocr_services import extract_ocr_text


file_path = Path(input("Enter invoice file path: ").strip().strip('"'))

try:
    if file_path.suffix.lower() == ".pdf":
        result = extract_pdf_text(file_path)

        print("\nPDF text extraction complete.")
        print("Pages:", result["page_count"])
        print("Needs OCR:", result["needs_ocr"])

        if result["needs_ocr"]:
            print("\nRunning OCR on the document...")
            result = extract_ocr_text(file_path)

    else:
        result = extract_ocr_text(file_path)

    print("\n--- EXTRACTED TEXT ---")
    print(result["text"] or "(No text extracted)")

    print("\n--- PAGE DETAILS ---")
    for page in result["pages"]:
        print(
            f"Page {page['page_number']}: "
            f"{page['extraction_method']}, "
            f"{len(page['text'])} characters"
        )

except Exception as exc:
    print(f"Extraction failed: {type(exc).__name__}: {exc}")