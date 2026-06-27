# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Tenant-level platform settings.

Platform-wide defaults come from environment variables (config.py).
Per-tenant overrides are stored in tenants.settings JSONB and layered on top.
Only users with role='admin' can write settings.
"""
from __future__ import annotations

from typing import Any
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select

from ..config import settings as platform_settings
from ..core.rls import tenant_context
from ..dependencies import CurrentUser, DbDep, TenantDep
from ..models.tenant import Tenant

router = APIRouter(prefix="/{tenant_slug}/settings/platform", tags=["settings"])

_ALL_PII_ENTITIES = [
    "PERSON",
    "EMAIL_ADDRESS",
    "PHONE_NUMBER",
    "US_SSN",
    "CREDIT_CARD",
    "IBAN_CODE",
    "MEDICAL_LICENSE",
    "DATE_TIME",
    "IP_ADDRESS",
    "URL",
    "NRP",
    "LOCATION",
    "ORGANIZATION",
]


# ── Schemas ────────────────────────────────────────────────────────────────────

class PiiSettings(BaseModel):
    enabled: bool = True
    language: str = "en"
    min_score: float = Field(0.5, ge=0.0, le=1.0)
    entities: list[str] = []


class ExtractionSettings(BaseModel):
    confidence_valid: float = Field(0.85, ge=0.0, le=1.0)
    confidence_review: float = Field(0.65, ge=0.0, le=1.0)
    confidence_flag: float = Field(0.7, ge=0.0, le=1.0)
    temperature: float = Field(0.0, ge=0.0, le=1.0)
    max_tokens: int = Field(4096, ge=256, le=8192)


class PipelineSettings(BaseModel):
    max_file_size_mb: int = Field(100, ge=1, le=500)
    max_pages: int = Field(500, ge=1, le=2000)
    timeout_seconds: int = Field(120, ge=30, le=600)
    ocr_workers: int = Field(4, ge=1, le=16)


class PlatformSettingsRead(BaseModel):
    pii: PiiSettings
    extraction: ExtractionSettings
    pipeline: PipelineSettings
    available_pii_entities: list[str]


class PlatformSettingsPatch(BaseModel):
    pii: PiiSettings | None = None
    extraction: ExtractionSettings | None = None
    pipeline: PipelineSettings | None = None


# ── Helpers ────────────────────────────────────────────────────────────────────

def _build_defaults() -> dict[str, Any]:
    """Build settings dict from platform environment variables."""
    return {
        "pii": {
            "enabled": platform_settings.pii_enabled,
            "language": platform_settings.pii_language,
            "min_score": platform_settings.pii_min_score,
            "entities": platform_settings.pii_entities,
        },
        "extraction": {
            "confidence_valid": platform_settings.extraction_confidence_valid,
            "confidence_review": platform_settings.extraction_confidence_review,
            "confidence_flag": platform_settings.extraction_confidence_flag,
            "temperature": platform_settings.extraction_temperature,
            "max_tokens": platform_settings.extraction_max_tokens,
        },
        "pipeline": {
            "max_file_size_mb": platform_settings.pipeline_max_file_size_mb,
            "max_pages": platform_settings.pipeline_max_pages,
            "timeout_seconds": platform_settings.pipeline_timeout_seconds,
            "ocr_workers": platform_settings.pipeline_ocr_workers,
        },
    }


def _merge(defaults: dict[str, Any], overrides: dict[str, Any]) -> dict[str, Any]:
    """Deep-merge overrides onto defaults (one level deep per group)."""
    merged = {k: dict(v) for k, v in defaults.items()}
    for group, values in overrides.items():
        if group in merged and isinstance(values, dict):
            merged[group].update(values)
    return merged


def _effective_settings(tenant: Tenant) -> dict[str, Any]:
    overrides: dict[str, Any] = (tenant.settings or {}).get("platform", {})
    return _merge(_build_defaults(), overrides)


# ── Routes ─────────────────────────────────────────────────────────────────────

@router.get("", response_model=PlatformSettingsRead)
async def get_platform_settings(
    tenant_slug: str,
    db: DbDep,
    current_user: CurrentUser,
    tenant: TenantDep,
) -> PlatformSettingsRead:
    effective = _effective_settings(tenant)
    return PlatformSettingsRead(
        pii=PiiSettings(**effective["pii"]),
        extraction=ExtractionSettings(**effective["extraction"]),
        pipeline=PipelineSettings(**effective["pipeline"]),
        available_pii_entities=_ALL_PII_ENTITIES,
    )


@router.patch("", response_model=PlatformSettingsRead)
async def update_platform_settings(
    tenant_slug: str,
    body: PlatformSettingsPatch,
    db: DbDep,
    current_user: CurrentUser,
    tenant: TenantDep,
) -> PlatformSettingsRead:
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can update platform settings",
        )

    # Load current overrides and apply the patch
    current_overrides: dict[str, Any] = dict(tenant.settings or {})
    platform_overrides: dict[str, Any] = current_overrides.get("platform", {})

    if body.pii is not None:
        platform_overrides["pii"] = body.pii.model_dump()
    if body.extraction is not None:
        platform_overrides["extraction"] = body.extraction.model_dump()
    if body.pipeline is not None:
        platform_overrides["pipeline"] = body.pipeline.model_dump()

    current_overrides["platform"] = platform_overrides

    async with tenant_context(db, tenant.id):
        result = await db.execute(
            select(Tenant).where(Tenant.id == tenant.id)
        )
        db_tenant = result.scalar_one()
        db_tenant.settings = current_overrides
        await db.commit()
        await db.refresh(db_tenant)

    effective = _effective_settings(db_tenant)
    return PlatformSettingsRead(
        pii=PiiSettings(**effective["pii"]),
        extraction=ExtractionSettings(**effective["extraction"]),
        pipeline=PipelineSettings(**effective["pipeline"]),
        available_pii_entities=_ALL_PII_ENTITIES,
    )


@router.delete("", status_code=status.HTTP_204_NO_CONTENT)
async def reset_platform_settings(
    tenant_slug: str,
    db: DbDep,
    current_user: CurrentUser,
    tenant: TenantDep,
) -> None:
    """Reset all platform settings to environment-variable defaults."""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can reset platform settings",
        )

    async with tenant_context(db, tenant.id):
        result = await db.execute(
            select(Tenant).where(Tenant.id == tenant.id)
        )
        db_tenant = result.scalar_one()
        current: dict[str, Any] = dict(db_tenant.settings or {})
        current.pop("platform", None)
        db_tenant.settings = current
        await db.commit()
