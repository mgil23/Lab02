# SPDX-License-Identifier: AGPL-3.0-or-later
import uuid
from sqlalchemy import JSON, UUID, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base import Base, TimestampMixin


class Tenant(Base, TimestampMixin):
    __tablename__ = "tenants"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    slug: Mapped[str] = mapped_column(String(63), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    plan: Mapped[str] = mapped_column(String(50), default="free", nullable=False)
    subscription_status: Mapped[str] = mapped_column(
        String(50), default="trialing", nullable=False
    )
    stripe_customer_id: Mapped[str | None] = mapped_column(
        String(255), unique=True
    )
    stripe_subscription_id: Mapped[str | None] = mapped_column(
        String(255), unique=True
    )
    settings: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)

    users: Mapped[list["User"]] = relationship(back_populates="tenant", cascade="all, delete-orphan")  # type: ignore[name-defined]
    documents: Mapped[list["Document"]] = relationship(back_populates="tenant", cascade="all, delete-orphan")  # type: ignore[name-defined]
