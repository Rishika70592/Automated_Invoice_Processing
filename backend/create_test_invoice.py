
import pymupdf
from pathlib import Path

output_path = Path(__file__).parent / "test-invoice.pdf"

doc = pymupdf.open()
page = doc.new_page()

page.insert_text((50, 60), "SYNTHETIC INVOICE", fontsize=20)
page.insert_text((50, 110), "Invoice Number: INV-1001", fontsize=12)
page.insert_text((50, 140), "Supplier: ABC Supplies", fontsize=12)
page.insert_text((50, 170), "Invoice Date: 2026-10-28", fontsize=12)
page.insert_text((50, 200), "Subtotal: 1000.00", fontsize=12)
page.insert_text((50, 230), "Tax: 180.00", fontsize=12)
page.insert_text((50, 260), "Total: 1180.00", fontsize=12)

doc.save(str(output_path), garbage=4, deflate=True)
doc.close()

print("Created:", output_path)
print("File size:", output_path.stat().st_size, "bytes")
