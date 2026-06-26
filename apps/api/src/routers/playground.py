# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Playground — single-shot extraction endpoint for testing document type schemas
without uploading a real file. Runs the full Strands Agent extraction pipeline
on raw text input and returns structured field results.
"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from sqlalchemy import select

from ..core.rls import tenant_context
from ..dependencies import CurrentUser, DbDep, TenantDep
from ..models.document_type import DocumentType

router = APIRouter(prefix="/{tenant_slug}/playground", tags=["playground"])


class PlaygroundRequest(BaseModel):
    document_type_slug: str
    text: str
    layout: dict | None = None


class PlaygroundFieldResult(BaseModel):
    field_name: str
    value: str | None
    confidence: float | None
    source_text: str | None
    reasoning: str | None
    validation_status: str


class PlaygroundResponse(BaseModel):
    document_type_slug: str
    fields: list[PlaygroundFieldResult]
    model_used: str
    tokens_used: int | None = None


@router.post("/extract", response_model=PlaygroundResponse)
async def playground_extract(
    tenant_slug: str,
    body: PlaygroundRequest,
    db: DbDep,
    current_user: CurrentUser,
    tenant: TenantDep,
) -> PlaygroundResponse:
    """
    Run extraction on raw text without creating a Document record.
    Returns extracted fields using the specified document type schema.
    """
    async with tenant_context(db, tenant.id):
        result = await db.execute(
            select(DocumentType).where(
                DocumentType.tenant_id == tenant.id,
                DocumentType.slug == body.document_type_slug,
                DocumentType.is_active.is_(True),
            )
        )
        doc_type = result.scalar_one_or_none()

    if not doc_type:
        raise HTTPException(status_code=404, detail="Document type not found")

    # Build config for ExtractionAgent
    await db.refresh(doc_type, ["fields", "validation_rules"])
    type_config = {
        "name": doc_type.name,
        "fields": [
            {
                "name": f.name,
                "label": f.label,
                "field_type": f.field_type,
                "is_required": f.is_required,
                "config": f.config,
            }
            for f in doc_type.fields
        ],
        "validation_rules": [
            {
                "field_name": r.field_name,
                "rule_type": r.rule_type,
                "rule_config": r.rule_config,
                "error_message": r.error_message,
            }
            for r in doc_type.validation_rules
        ],
        "extraction_rules": doc_type.extraction_rules,
    }

    model_used = "unknown"
    tokens_used: int | None = None
    fields: list[PlaygroundFieldResult] = []

    try:
        from strands_idp.agent import ExtractionAgent
        from ..config import settings

        agent = ExtractionAgent(type_config)
        raw = await agent.run(
            text=body.text,
            layout=body.layout or {},
            page_range=(1, 1),
        )
        model_used = settings.bedrock_model_id

        for field_name, info in raw.items():
            if not isinstance(info, dict):
                continue
            fields.append(
                PlaygroundFieldResult(
                    field_name=field_name,
                    value=str(info.get("value")) if info.get("value") is not None else None,
                    confidence=info.get("confidence"),
                    source_text=info.get("source_text"),
                    reasoning=info.get("reasoning"),
                    validation_status="pending",
                )
            )
    except Exception:
        # Graceful fallback: return empty field stubs with schema names
        model_used = "fallback"
        for f in type_config["fields"]:
            fields.append(
                PlaygroundFieldResult(
                    field_name=f["name"],
                    value=None,
                    confidence=None,
                    source_text=None,
                    reasoning="Extraction service unavailable",
                    validation_status="pending",
                )
            )

    return PlaygroundResponse(
        document_type_slug=body.document_type_slug,
        fields=fields,
        model_used=model_used,
        tokens_used=tokens_used,
    )
