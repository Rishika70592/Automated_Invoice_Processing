
from datetime import datetime, timezone
import uuid

from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Index,
    JSON,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from app.db.database import Base




class DocumentSource(Base):
    __tablename__ = "document_sources"

    id = Column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )

    document_id = Column(
        String(36),
        ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # manual_upload, gmail, microsoft_graph, s3, bulk_import
    source_type = Column(String(40), nullable=False, index=True)

    # Stable identifier for the source item:
    # Gmail: message_id:attachment_id
    # S3: bucket:key:version_id (or bucket:key:etag)
    # Bulk: import_id:relative_file_path
    source_reference = Column(String(1000), nullable=False)

    # Optional source-specific information
    source_metadata = Column(JSON, nullable=True)

    # received, registered, processing, completed, failed, duplicate
    status = Column(
        String(30),
        nullable=False,
        default="registered",
        index=True,
    )

    file_hash = Column(String(64), nullable=True, index=True)

    error_message = Column(String(2000), nullable=True)

    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    document = relationship(
        "Document",
        back_populates="sources",
    )

    __table_args__ = (
        UniqueConstraint(
            "source_type",
            "source_reference",
            name="uq_document_source_reference",
        ),
        Index(
            "ix_document_sources_type_reference",
            "source_type",
            "source_reference",
        ),
    )
