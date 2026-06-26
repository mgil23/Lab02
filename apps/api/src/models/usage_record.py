# SPDX-License-Identifier: AGPL-3.0-or-later
import uuid
from datetime import datetime
from decimal import Decimal
from sqlalchemy import UUID, DateTime, Index, JSON, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column
from .base import Base, TenantScopedMixin


class UsageRecord(Base, TenantScopedMixin):
    __tablename__ = "usage_records"
    __table_args__ = (
        Index("idx_usage_tenant_metric_date", "tenant_id", "metric", "recorded_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    metric: Mapped[str] = mapped_column(String(100), nullable=False)
    quantity: Mapped[Decimal] = mapped_column(Numeric, nullable=False)
    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    stripe_usage_record_id: Mapped[str | None] = mapped_column(String(255))
    metadata_: Mapped[dict | None] = mapped_column(JSON, name="metadata")
