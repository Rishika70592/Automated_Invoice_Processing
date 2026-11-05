import uuid
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
    Date,
    DateTime,
    ForeignKey,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base





class Invoice(Base):
    __tablename__ = "invoices"

    __table_args__ = (
        UniqueConstraint(
            "document_id",
            name="uq_invoice_document_id",
        ),
    )

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )

    document_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("documents.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    supplier_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("suppliers.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    invoice_number: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        index=True,
    )

    purchase_order_number: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    invoice_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    due_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    currency: Mapped[str | None] = mapped_column(
        String(10),
        nullable=True,
    )

    payment_terms: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    subtotal: Mapped[Decimal | None] = mapped_column(
        Numeric(18, 4),
        nullable=True,
    )

    tax: Mapped[Decimal | None] = mapped_column(
        Numeric(18, 4),
        nullable=True,
    )

    discount: Mapped[Decimal | None] = mapped_column(
        Numeric(18, 4),
        nullable=True,
    )

    total_amount: Mapped[Decimal | None] = mapped_column(
        Numeric(18, 4),
        nullable=True,
    )

    extraction_method: Mapped[str | None] = mapped_column(
        String(30),
        nullable=True,
    )

    model_name: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    document: Mapped["Document"] = relationship( # type: ignore
    "Document",
    back_populates="invoice",
    )

    supplier: Mapped["Supplier | None"] = relationship( # type: ignore
    "Supplier",
    back_populates="invoices",
    )

    line_items: Mapped[list["InvoiceLineItem"]] = relationship( # type: ignore
        "InvoiceLineItem",
        back_populates="invoice",
        cascade="all, delete-orphan",
        order_by="InvoiceLineItem.id",
    )

    validation_results: Mapped[list["ValidationResult"]] = relationship( # type: ignore
        "ValidationResult",
        back_populates="invoice",
    )