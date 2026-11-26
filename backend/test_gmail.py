
from app.services.gmail_invoice_service import (
    process_gmail_invoices
)

if __name__ == "__main__":

    print("Starting Gmail invoice processing...")

    result = process_gmail_invoices(max_results=20)

    print("\n========== GMAIL RESULTS ==========")

    print("Emails found:", result["emails_found"])
    print("Attachments found:", result["attachments_found"])
    print("Invoices processed:", result["invoices_processed"])
    print("Non-invoices skipped:", result["non_invoices_skipped"])
    print("Failed:", result["failed"])

    print("\nDetailed results:")

    for item in result["details"]:
        print(item)

    print("\nGmail processing finished.")
