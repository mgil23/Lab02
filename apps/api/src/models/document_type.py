# SPDX-License-Identifier: AGPL-3.0-or-later
import uuid
from sqlalchemy import UUID, Boolean, ForeignKey, Integer, JSON, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base import Base, TimestampMixin, TenantScopedMixin


class DocumentType(Base, TimestampMixin, TenantScopedMixin):
    __tablename__ = "document_types"
    __table_args__ = (UniqueConstraint("tenant_id", "slug"),)

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    classification_hints: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    extraction_rules: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    fields: Mapped[list["DocumentTypeField"]] = relationship(
        back_populates="document_type", cascade="all, delete-orphan",
        order_by="DocumentTypeField.sort_order"
    )
    validation_rules: Mapped[list["ValidationRule"]] = relationship(
        back_populates="document_type", cascade="all, delete-orphan",
        order_by="ValidationRule.sort_order"
    )


class DocumentTypeField(Base, TenantScopedMixin):
    __tablename__ = "document_type_fields"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    document_type_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("document_types.id", ondelete="CASCADE"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    label: Mapped[str] = mapped_column(String(255), nullable=False)
    field_type: Mapped[str] = mapped_column(String(50), nullable=False)
    is_required: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    config: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)

    document_type: Mapped["DocumentType"] = relationship(back_populates="fields")


class ValidationRule(Base, TenantScopedMixin):
    __tablename__ = "validation_rules"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    document_type_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("document_types.id", ondelete="CASCADE"),
        nullable=False,
    )
    field_name: Mapped[str | None] = mapped_column(String(255))
    rule_type: Mapped[str] = mapped_column(String(50), nullable=False)
    rule_config: Mapped[dict] = mapped_column(JSON, nullable=False)
    error_message: Mapped[str] = mapped_column(String(500), nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    document_type: Mapped["DocumentType"] = relationship(back_populates="validation_rules")
