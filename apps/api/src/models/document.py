# SPDX-License-Identifier: AGPL-3.0-or-later
import uuid
from enum import Enum
from sqlalchemy import UUID, BigInteger, ForeignKey, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base import Base, TimestampMixin, TenantScopedMixin


class DocumentStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    NEEDS_REVIEW = "needs_review"


class Document(Base, TimestampMixin, TenantScopedMixin):
    __tablename__ = "documents"
    __table_args__ = (
        Index("idx_documents_tenant_status", "tenant_id", "status"),
        Index("idx_documents_tenant_created", "tenant_id", "created_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    filename: Mapped[str] = mapped_column(String(500), nullable=False)
    storage_key: Mapped[str] = mapped_column(String(1000), nullable=False)
    file_size: Mapped[int] = mapped_column(BigInteger, nullable=False)
    page_count: Mapped[int | None] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(
        String(50), default=DocumentStatus.PENDING, nullable=False
    )
    pipeline_run_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL")
    )

    tenant: Mapped["Tenant"] = relationship(back_populates="documents")  # type: ignore[name-defined]
    subdocuments: Mapped[list["SubDocument"]] = relationship(  # type: ignore[name-defined]
        back_populates="document", cascade="all, delete-orphan"
    )
    pipeline_runs: Mapped[list["PipelineRun"]] = relationship(  # type: ignore[name-defined]
        back_populates="document", cascade="all, delete-orphan"
    )
