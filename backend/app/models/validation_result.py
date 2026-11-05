import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import (
    DateTime,
    ForeignKey,
    JSON,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base



class ValidationResult(Base):
    __tablename__ = "validation_results"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )

    document_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    invoice_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("invoices.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
    )

    errors: Mapped[list[Any]] = mapped_column(
        JSON,
        default=list,
        nullable=False,
    )

    warnings: Mapped[list[Any]] = mapped_column(
        JSON,
        default=list,
        nullable=False,
    )

    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    validated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    invoice: Mapped["Invoice | None"] = relationship( # type: ignore
        "Invoice",
        back_populates="validation_results",
    )

    document: Mapped["Document"] = relationship( # type: ignore
        "Document",
        back_populates="validation_results",
    )