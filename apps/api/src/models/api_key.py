# SPDX-License-Identifier: AGPL-3.0-or-later
import uuid
from datetime import datetime
from sqlalchemy import ARRAY, UUID, DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base import Base, TenantScopedMixin


class ApiKey(Base, TenantScopedMixin):
    __tablename__ = "api_keys"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE")
    )
    key_hash: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    scopes: Mapped[list[str]] = mapped_column(ARRAY(String), default=list, nullable=False)
    last_used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )

    user: Mapped["User | None"] = relationship(back_populates="api_keys")  # type: ignore[name-defined]
