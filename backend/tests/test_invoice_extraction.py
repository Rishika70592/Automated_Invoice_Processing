
from unittest.mock import patch

from app.services.invoice_extractor_service import (
    extract_invoice_data,
)


def test_extract_invoice_data():
    fake_response = {
        "response": """
        {
            "invoice_number": "INV-001",
            "supplier_name": "ABC Technologies",
            "supplier_tax_id": null,
            "purchase_order_number": null,
            "invoice_date": "2026-11-10",
            "due_date": "2026-11-20",
            "currency": "USD",
            "payment_terms": "Net 10",
            "subtotal": "1000.00",
            "tax": "100.00",
            "discount": "0.00",
            "total_amount": "1100.00",
            "line_items": [],
            "missing_fields": [],
            "uncertainty_notes": []
        }
        """
    }

    with patch(
        "app.services.invoice_extractor_service.httpx.Client"
    ) as mock_client:

        mock_instance = mock_client.return_value.__enter__.return_value

        mock_instance.post.return_value.raise_for_status.return_value = None
        mock_instance.post.return_value.json.return_value = fake_response

        result = extract_invoice_data(
            "Invoice Number: INV-001"
        )

    assert result.data.invoice_number == "INV-001"
    assert result.data.supplier_name == "ABC Technologies"
    assert result.data.total_amount == 1100
    assert result.extraction_method == "llm"
    assert result.model_name == "llama3.2:3b"
    assert result.data.invoice_date.isoformat() == "2026-11-10"
    assert result.data.due_date.isoformat() == "2026-11-20"

    assert result.data.subtotal == 1000
    assert result.data.tax == 100
    assert result.data.discount == 0

    assert result.data.currency == "USD"
    assert result.data.line_items == []