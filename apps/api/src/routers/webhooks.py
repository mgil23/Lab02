# SPDX-License-Identifier: AGPL-3.0-or-later
from __future__ import annotations

import hashlib
import secrets
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, HttpUrl, field_validator
from sqlalchemy import select

from ..core.rls import tenant_context
from ..dependencies import CurrentUser, DbDep, TenantDep
from ..models.webhook import Webhook

router = APIRouter(prefix="/{tenant_slug}/webhooks", tags=["webhooks"])

_ALLOWED_EVENTS = [
    "document.completed",
    "document.failed",
    "document.needs_review",
    "extraction.field_updated",
]


# ── Schemas ────────────────────────────────────────────────────────────────────

class WebhookRead(BaseModel):
    id: uuid.UUID
    url: str
    events: list[str]
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class WebhookCreate(BaseModel):
    url: str
    events: list[str]

    @field_validator("events")
    @classmethod
    def validate_events(cls, v: list[str]) -> list[str]:
        invalid = [e for e in v if e not in _ALLOWED_EVENTS]
        if invalid:
            raise ValueError(f"Unknown events: {invalid}. Allowed: {_ALLOWED_EVENTS}")
        if not v:
            raise ValueError("At least one event is required")
        return v


class WebhookCreateResponse(BaseModel):
    webhook: WebhookRead
    # Raw secret shown once only — used to verify X-OpenIDP-Signature headers
    secret: str


class WebhookPatch(BaseModel):
    events: list[str] | None = None
    is_active: bool | None = None

    @field_validator("events")
    @classmethod
    def validate_events(cls, v: list[str] | None) -> list[str] | None:
        if v is None:
            return v
        invalid = [e for e in v if e not in _ALLOWED_EVENTS]
        if invalid:
            raise ValueError(f"Unknown events: {invalid}")
        return v


# ── Routes ─────────────────────────────────────────────────────────────────────

@router.get("", response_model=list[WebhookRead])
async def list_webhooks(
    tenant_slug: str,
    db: DbDep,
    current_user: CurrentUser,
    tenant: TenantDep,
) -> list[WebhookRead]:
    async with tenant_context(db, tenant.id):
        result = await db.execute(
            select(Webhook)
            .where(Webhook.tenant_id == tenant.id)
            .order_by(Webhook.created_at.desc())
        )
        webhooks = result.scalars().all()
    return [WebhookRead.model_validate(w) for w in webhooks]


@router.post("", response_model=WebhookCreateResponse, status_code=status.HTTP_201_CREATED)
async def create_webhook(
    tenant_slug: str,
    body: WebhookCreate,
    db: DbDep,
    current_user: CurrentUser,
    tenant: TenantDep,
) -> WebhookCreateResponse:
    if current_user.role not in ("admin",):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can create webhooks",
        )

    raw_secret = f"whsec_{secrets.token_urlsafe(32)}"
    secret_hash = hashlib.sha256(raw_secret.encode()).hexdigest()

    webhook = Webhook(
        tenant_id=tenant.id,
        url=str(body.url),
        events=body.events,
        secret_hash=secret_hash,
        is_active=True,
        created_at=datetime.now(timezone.utc),
    )
    db.add(webhook)
    await db.commit()
    await db.refresh(webhook)

    return WebhookCreateResponse(
        webhook=WebhookRead.model_validate(webhook),
        secret=raw_secret,
    )


@router.patch("/{webhook_id}", response_model=WebhookRead)
async def update_webhook(
    tenant_slug: str,
    webhook_id: uuid.UUID,
    body: WebhookPatch,
    db: DbDep,
    current_user: CurrentUser,
    tenant: TenantDep,
) -> WebhookRead:
    if current_user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admins only")

    async with tenant_context(db, tenant.id):
        result = await db.execute(
            select(Webhook).where(
                Webhook.id == webhook_id,
                Webhook.tenant_id == tenant.id,
            )
        )
        webhook = result.scalar_one_or_none()

    if not webhook:
        raise HTTPException(status_code=404, detail="Webhook not found")

    if body.events is not None:
        webhook.events = body.events
    if body.is_active is not None:
        webhook.is_active = body.is_active

    await db.commit()
    await db.refresh(webhook)
    return WebhookRead.model_validate(webhook)


@router.delete("/{webhook_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_webhook(
    tenant_slug: str,
    webhook_id: uuid.UUID,
    db: DbDep,
    current_user: CurrentUser,
    tenant: TenantDep,
) -> None:
    if current_user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admins only")

    async with tenant_context(db, tenant.id):
        result = await db.execute(
            select(Webhook).where(
                Webhook.id == webhook_id,
                Webhook.tenant_id == tenant.id,
            )
        )
        webhook = result.scalar_one_or_none()

    if not webhook:
        raise HTTPException(status_code=404, detail="Webhook not found")

    await db.delete(webhook)
    await db.commit()
