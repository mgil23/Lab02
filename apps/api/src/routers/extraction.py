# SPDX-License-Identifier: AGPL-3.0-or-later
import uuid
from fastapi import APIRouter, HTTPException
from sqlalchemy import select
from ..dependencies import DbDep, CurrentUser, TenantDep
from ..models.extracted_field import ExtractedField
from ..models.subdocument import SubDocument
from ..schemas.extraction import ExtractedFieldRead, ExtractedFieldUpdate, ExtractionSummary
from ..core.rls import tenant_context

router = APIRouter(prefix="/{tenant_slug}/extraction", tags=["extraction"])


@router.get("/fields", response_model=ExtractionSummary)
async def get_fields(
    tenant_slug: str,
    subdocument_id: uuid.UUID,
    db: DbDep,
    current_user: CurrentUser,
    tenant: TenantDep,
) -> ExtractionSummary:
    async with tenant_context(db, tenant.id):
        result = await db.execute(
            select(ExtractedField)
            .where(
                ExtractedField.subdocument_id == subdocument_id,
                ExtractedField.tenant_id == tenant.id,
            )
            .order_by(ExtractedField.created_at)
        )
        fields = result.scalars().all()

    field_reads = [ExtractedFieldRead.model_validate(f) for f in fields]
    return ExtractionSummary(
        subdocument_id=subdocument_id,
        total_fields=len(fields),
        validated=sum(1 for f in fields if f.validation_status == "valid"),
        flagged=sum(1 for f in fields if f.validation_status == "flagged"),
        human_reviewed=sum(1 for f in fields if f.human_reviewed),
        fields=field_reads,
    )


@router.patch("/fields/{field_id}", response_model=ExtractedFieldRead)
async def update_field(
    tenant_slug: str,
    field_id: uuid.UUID,
    body: ExtractedFieldUpdate,
    db: DbDep,
    current_user: CurrentUser,
    tenant: TenantDep,
) -> ExtractedFieldRead:
    async with tenant_context(db, tenant.id):
        result = await db.execute(
            select(ExtractedField).where(
                ExtractedField.id == field_id,
                ExtractedField.tenant_id == tenant.id,
            )
        )
        field = result.scalar_one_or_none()
    if not field:
        raise HTTPException(status_code=404, detail="Field not found")

    field.human_value = body.human_value
    field.human_reviewed = body.human_reviewed
    field.validation_status = "human_reviewed"
    await db.commit()
    await db.refresh(field)
    return ExtractedFieldRead.model_validate(field)


@router.get("/subdocuments/{document_id}", response_model=list[dict])
async def list_subdocuments(
    tenant_slug: str,
    document_id: uuid.UUID,
    db: DbDep,
    current_user: CurrentUser,
    tenant: TenantDep,
) -> list[dict]:
    async with tenant_context(db, tenant.id):
        result = await db.execute(
            select(SubDocument)
            .where(
                SubDocument.document_id == document_id,
                SubDocument.tenant_id == tenant.id,
            )
            .order_by(SubDocument.created_at)
        )
        subdocs = result.scalars().all()

    return [
        {
            "id": str(s.id),
            "document_id": str(s.document_id),
            "document_type_id": str(s.document_type_id) if s.document_type_id else None,
            "page_count": s.page_count,
            "page_start": s.page_range.lower,
            "page_end": s.page_range.upper,
            "status": s.status,
            "classification_confidence": float(s.classification_confidence) if s.classification_confidence else None,
            "storage_key": s.storage_key,
            "split_signals": s.split_signals,
        }
        for s in subdocs
    ]
