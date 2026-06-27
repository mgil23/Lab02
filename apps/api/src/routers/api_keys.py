# SPDX-License-Identifier: AGPL-3.0-or-later
from __future__ import annotations

import uuid
from datetime import datetime, UTC

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, ConfigDict
from sqlalchemy import select

from ..core.rls import tenant_context
from ..core.security import generate_api_key
from ..dependencies import CurrentUser, DbDep, TenantDep
from ..models.api_key import ApiKey

router = APIRouter(prefix="/{tenant_slug}/api-keys", tags=["api-keys"])


class ApiKeyCreate(BaseModel):
    name: str
    scopes: list[str] = []
    expires_days: int | None = None


class ApiKeyRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    key_prefix: str
    scopes: list[str]
    last_used_at: datetime | None
    expires_at: datetime | None
    created_at: datetime


class ApiKeyCreateResponse(BaseModel):
    """Returned once at creation — contains the raw key. Never returned again."""
    key: str
    api_key: ApiKeyRead


@router.get("", response_model=list[ApiKeyRead])
async def list_api_keys(
    tenant_slug: str,
    db: DbDep,
    current_user: CurrentUser,
    tenant: TenantDep,
) -> list[ApiKeyRead]:
    async with tenant_context(db, tenant.id):
        result = await db.execute(
            select(ApiKey)
            .where(ApiKey.tenant_id == tenant.id)
            .order_by(ApiKey.created_at.desc())
        )
        keys = result.scalars().all()
    return [ApiKeyRead.model_validate(k) for k in keys]


@router.post("", response_model=ApiKeyCreateResponse, status_code=status.HTTP_201_CREATED)
async def create_api_key(
    tenant_slug: str,
    body: ApiKeyCreate,
    db: DbDep,
    current_user: CurrentUser,
    tenant: TenantDep,
) -> ApiKeyCreateResponse:
    plain_key, key_hash = generate_api_key()
    # key_prefix = first 12 chars after 'oidp_' for display
    key_prefix = plain_key[:12]

    expires_at = None
    if body.expires_days:
        from datetime import timedelta
        expires_at = datetime.now(UTC) + timedelta(days=body.expires_days)

    api_key = ApiKey(
        tenant_id=tenant.id,
        user_id=current_user.id,
        key_hash=key_hash,
        key_prefix=key_prefix,
        name=body.name,
        scopes=body.scopes,
        expires_at=expires_at,
        created_at=datetime.now(UTC),
    )
    db.add(api_key)
    await db.commit()
    await db.refresh(api_key)

    return ApiKeyCreateResponse(
        key=plain_key,
        api_key=ApiKeyRead.model_validate(api_key),
    )


@router.delete("/{key_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_api_key(
    tenant_slug: str,
    key_id: uuid.UUID,
    db: DbDep,
    current_user: CurrentUser,
    tenant: TenantDep,
) -> None:
    async with tenant_context(db, tenant.id):
        result = await db.execute(
            select(ApiKey).where(
                ApiKey.id == key_id,
                ApiKey.tenant_id == tenant.id,
            )
        )
        api_key = result.scalar_one_or_none()
    if not api_key:
        raise HTTPException(status_code=404, detail="API key not found")
    await db.delete(api_key)
    await db.commit()
