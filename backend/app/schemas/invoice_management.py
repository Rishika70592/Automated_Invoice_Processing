
from datetime import date
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class InvoiceLineItemUpdate(BaseModel):
    """Schema for manually correcting an invoice line item."""

    model_config = ConfigDict(extra="forbid")

    description: str | None = None
    quantity: Decimal | None = None
    unit_price: Decimal | None = None
    tax_rate: Decimal | None = None
    tax_amount: Decimal | None = None
    line_total: Decimal | None = None


class SupplierUpdate(BaseModel):
    """Schema for correcting supplier information."""

    model_config = ConfigDict(extra="forbid")

    name: str | None = None
    tax_id: str | None = None
    email: str | None = None
    phone: str | None = None
    address: str | None = None


class InvoiceUpdate(BaseModel):
    """Schema for manually updating extracted invoice information."""

    model_config = ConfigDict(extra="forbid")

    invoice_number: str | None = None
    purchase_order_number: str | None = None

    invoice_date: date | None = None
    due_date: date | None = None

    currency: str | None = None
    payment_terms: str | None = None

    subtotal: Decimal | None = None
    tax: Decimal | None = None
    discount: Decimal | None = None
    total_amount: Decimal | None = None

    supplier: SupplierUpdate | None = None

    line_items: list[InvoiceLineItemUpdate] | None = None
