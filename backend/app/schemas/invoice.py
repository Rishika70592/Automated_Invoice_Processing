
from datetime import date
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class InvoiceLineItem(BaseModel):
    """A single line item extracted from an invoice."""

    model_config = ConfigDict(extra="forbid")

    description: str | None = None
    quantity: Decimal | None = None
    unit_price: Decimal | None = None
    tax_rate: Decimal | None = None
    tax_amount: Decimal | None = None
    line_total: Decimal | None = None


class InvoiceData(BaseModel):
    """Structured invoice information returned by the extractor."""

    model_config = ConfigDict(extra="forbid")

    invoice_number: str | None = None
    supplier_name: str | None = None
    supplier_tax_id: str | None = None
    purchase_order_number: str | None = None

    invoice_date: date | None = None
    due_date: date | None = None

    currency: str | None = None
    payment_terms: str | None = None

    subtotal: Decimal | None = None
    tax: Decimal | None = None
    discount: Decimal | None = None
    total_amount: Decimal | None = None

    line_items: list[InvoiceLineItem] = Field(default_factory=list)

    missing_fields: list[str] = Field(default_factory=list)
    uncertainty_notes: list[str] = Field(default_factory=list)


class InvoiceExtractionResult(BaseModel):
    """Extraction result, including provenance and review information."""

    model_config = ConfigDict(extra="forbid")

    data: InvoiceData
    original_text: str
    extraction_method: Literal["llm"] = "llm"
    model_name: str
    confidence: Decimal | None = None

    @field_validator("confidence")
    @classmethod
    def validate_confidence(
        cls, value: Decimal | None
    ) -> Decimal | None:
        if value is not None and not Decimal("0") <= value <= Decimal("1"):
            raise ValueError("Confidence must be between 0 and 1.")
        return value
