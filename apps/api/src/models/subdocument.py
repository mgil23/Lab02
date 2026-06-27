# SPDX-License-Identifier: AGPL-3.0-or-later
import uuid
from decimal import Decimal
from typing import Any
from sqlalchemy import UUID, ForeignKey, Index, Integer, JSON, Numeric, String
from sqlalchemy.dialects.postgresql import INT4RANGE
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base import Base, TimestampMixin, TenantScopedMixin


class SubDocument(Base, TimestampMixin, TenantScopedMixin):
    __tablename__ = "subdocuments"
    __table_args__ = (
        Index("idx_subdocuments_document", "document_id"),
        Index("idx_subdocuments_page_range", "page_range", postgresql_using="gist"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    document_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=False,
    )
    document_type_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("document_types.id", ondelete="SET NULL")
    )
    page_range: Mapped[Any] = mapped_column(INT4RANGE, nullable=False)
    page_count: Mapped[int] = mapped_column(Integer, nullable=False)
    storage_key: Mapped[str | None] = mapped_column(String(1000))
    status: Mapped[str] = mapped_column(String(50), default="pending", nullable=False)
    classification_confidence: Mapped[Decimal | None] = mapped_column(Numeric(5, 4))
    classification_model: Mapped[str | None] = mapped_column(String(100))
    split_signals: Mapped[dict | None] = mapped_column(JSON)

    document: Mapped["Document"] = relationship(back_populates="subdocuments")  # type: ignore[name-defined]
    document_type: Mapped["DocumentType | None"] = relationship()  # type: ignore[name-defined]
    extracted_fields: Mapped[list["ExtractedField"]] = relationship(  # type: ignore[name-defined]
        back_populates="subdocument", cascade="all, delete-orphan"
    )
