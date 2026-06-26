# SPDX-License-Identifier: AGPL-3.0-or-later
import uuid
from datetime import datetime, UTC
from sqlalchemy import UUID, ForeignKey, Integer, JSON, String, Text, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base import Base, TimestampMixin, TenantScopedMixin


class PipelineRun(Base, TimestampMixin, TenantScopedMixin):
    __tablename__ = "pipeline_runs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    document_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=False,
    )
    status: Mapped[str] = mapped_column(String(50), default="queued", nullable=False)
    stages: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    total_duration_ms: Mapped[int | None] = mapped_column(Integer)
    error_message: Mapped[str | None] = mapped_column(Text)
    otel_trace_id: Mapped[str | None] = mapped_column(String(32))

    document: Mapped["Document"] = relationship(back_populates="pipeline_runs")  # type: ignore[name-defined]

    @classmethod
    async def create(
        cls, db: AsyncSession, document_id: uuid.UUID, tenant_id: uuid.UUID
    ) -> "PipelineRun":
        run = cls(document_id=document_id, tenant_id=tenant_id, status="running")
        db.add(run)
        await db.flush()
        return run

    async def start_stage(self, db: AsyncSession, stage: str) -> None:
        stages = dict(self.stages)
        stages[stage] = {"started_at": datetime.now(UTC).isoformat(), "status": "running"}
        self.stages = stages
        self.status = "running"
        await db.flush()

    async def complete_stage(self, db: AsyncSession, stage: str) -> None:
        stages = dict(self.stages)
        if stage in stages:
            stages[stage]["ended_at"] = datetime.now(UTC).isoformat()
            stages[stage]["status"] = "completed"
        self.stages = stages
        await db.flush()

    async def fail_stage(self, db: AsyncSession, stage: str, error: str) -> None:
        stages = dict(self.stages)
        stages[stage] = {
            **stages.get(stage, {}),
            "ended_at": datetime.now(UTC).isoformat(),
            "status": "failed",
            "error": error,
        }
        self.stages = stages
        await db.flush()

    async def mark_failed(self, db: AsyncSession, error: str) -> None:
        self.status = "failed"
        self.error_message = error
        await db.flush()

    async def mark_completed(self, db: AsyncSession, duration_ms: int) -> None:
        self.status = "completed"
        self.total_duration_ms = duration_ms
        await db.flush()
