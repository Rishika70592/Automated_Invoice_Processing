
import uuid
from datetime import datetime

from sqlalchemy import (
    BigInteger,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )

    uploaded_by_user_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    original_filename: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    stored_filename: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False,
    )

    storage_path: Mapped[str] = mapped_column(
        String(1000),
        nullable=False,
    )

    content_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    file_size: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
    )

    sha256_hash: Mapped[str] = mapped_column(
        String(64),
        index=True,
        nullable=False,
    )

    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="uploaded",
        server_default="uploaded",
    )

    uploaded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    extracted_text: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    extraction_method: Mapped[str | None] = mapped_column(
        String(30),
        nullable=True,
    )

    page_count: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    extraction_error: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    extracted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Relationships

    uploaded_by_user: Mapped["User | None"] = relationship( # type: ignore
        "User",
        back_populates="documents",
    )

    invoice: Mapped["Invoice | None"] = relationship( # type: ignore
        "Invoice",
        back_populates="document",
        uselist=False,
    )

    processing_jobs: Mapped[list["ProcessingJob"]] = relationship( # type: ignore
        "ProcessingJob",
        back_populates="document",
        cascade="all, delete-orphan",
    )

    validation_results: Mapped[list["ValidationResult"]] = relationship( # type: ignore
        "ValidationResult",
        back_populates="document",
        cascade="all, delete-orphan",
    )

    audit_logs: Mapped[list["AuditLog"]] = relationship( # type: ignore
        "AuditLog",
        back_populates="document",
    )
