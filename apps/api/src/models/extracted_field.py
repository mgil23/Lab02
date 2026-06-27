# SPDX-License-Identifier: AGPL-3.0-or-later
import uuid
from decimal import Decimal
from sqlalchemy import UUID, Boolean, ForeignKey, Index, Integer, JSON, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base import Base, TimestampMixin, TenantScopedMixin


class ExtractedField(Base, TimestampMixin, TenantScopedMixin):
    __tablename__ = "extracted_fields"
    __table_args__ = (
        Index("idx_extracted_fields_subdoc", "subdocument_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    subdocument_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("subdocuments.id", ondelete="CASCADE"),
        nullable=False,
    )
    field_name: Mapped[str] = mapped_column(String(255), nullable=False)
    field_value: Mapped[str | None] = mapped_column(Text)
    confidence: Mapped[Decimal | None] = mapped_column(Numeric(5, 4))
    page_number: Mapped[int | None] = mapped_column(Integer)
    bounding_box: Mapped[dict | None] = mapped_column(JSON)
    source_text: Mapped[str | None] = mapped_column(Text)
    reasoning: Mapped[str | None] = mapped_column(Text)
    extraction_method: Mapped[str] = mapped_column(String(50), default="llm", nullable=False)
    validation_status: Mapped[str] = mapped_column(String(50), default="pending", nullable=False)
    validation_errors: Mapped[list | None] = mapped_column(JSON)
    human_reviewed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    human_value: Mapped[str | None] = mapped_column(Text)

    subdocument: Mapped["SubDocument"] = relationship(back_populates="extracted_fields")  # type: ignore[name-defined]
