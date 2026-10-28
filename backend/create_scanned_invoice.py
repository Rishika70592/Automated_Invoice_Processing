
from pathlib import Path
import pymupdf

output_path = Path(__file__).parent / "scanned-test-invoice.pdf"

# Create an image containing invoice text.
image_doc = pymupdf.open()
image_page = image_doc.new_page(width=595, height=842)

image_page.insert_text((50, 60), "SYNTHETIC INVOICE", fontsize=20)
image_page.insert_text((50, 110), "Invoice Number: OCR-2001", fontsize=14)
image_page.insert_text((50, 150), "Supplier: Test Supplies Ltd", fontsize=14)
image_page.insert_text((50, 190), "Subtotal: 2000.00", fontsize=14)
image_page.insert_text((50, 230), "Tax: 360.00", fontsize=14)
image_page.insert_text((50, 270), "Total: 2360.00", fontsize=14)

# Render the page as an image.
pix = image_page.get_pixmap(dpi=200, alpha=False)
image_bytes = pix.tobytes("png")
image_doc.close()

# Embed only the rendered image in a new PDF.
scanned_doc = pymupdf.open()
scanned_page = scanned_doc.new_page(width=595, height=842)
scanned_page.insert_image(scanned_page.rect, stream=image_bytes)

scanned_doc.save(str(output_path))
scanned_doc.close()

print(f"Created scanned-style PDF: {output_path}")
