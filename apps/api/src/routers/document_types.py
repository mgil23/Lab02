# SPDX-License-Identifier: AGPL-3.0-or-later
from __future__ import annotations

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from ..core.rls import tenant_context
from ..dependencies import CurrentUser, DbDep, TenantDep
from ..models.document_type import DocumentType, DocumentTypeField, ValidationRule
from ..schemas.document_type import (
    DocumentTypeCreate,
    DocumentTypeRead,
    DocumentTypeUpdate,
    FieldDefinition,
    ValidationRuleDefinition,
)

router = APIRouter(prefix="/{tenant_slug}/document-types", tags=["document-types"])


@router.post("", response_model=DocumentTypeRead, status_code=status.HTTP_201_CREATED)
async def create_document_type(
    tenant_slug: str,
    body: DocumentTypeCreate,
    db: DbDep,
    current_user: CurrentUser,
    tenant: TenantDep,
) -> DocumentTypeRead:
    async with tenant_context(db, tenant.id):
        dup = await db.execute(
            select(DocumentType).where(
                DocumentType.tenant_id == tenant.id,
                DocumentType.slug == body.slug,
            )
        )
        if dup.scalar_one_or_none():
            raise HTTPException(status_code=409, detail="Slug already exists for this tenant")

        dt = DocumentType(
            tenant_id=tenant.id,
            name=body.name,
            slug=body.slug,
            description=body.description,
            classification_hints=body.classification_hints,
            extraction_rules=body.extraction_rules,
        )
        db.add(dt)
        await db.flush()

        for i, f in enumerate(body.fields):
            db.add(DocumentTypeField(
                tenant_id=tenant.id,
                document_type_id=dt.id,
                **{**f.model_dump(), "sort_order": f.sort_order or i},
            ))

        for i, r in enumerate(body.validation_rules):
            db.add(ValidationRule(
                tenant_id=tenant.id,
                document_type_id=dt.id,
                **{**r.model_dump(), "sort_order": r.sort_order or i},
            ))

    await db.commit()
    await db.refresh(dt)
    return DocumentTypeRead.model_validate(dt)


@router.get("", response_model=list[DocumentTypeRead])
async def list_document_types(
    tenant_slug: str,
    db: DbDep,
    current_user: CurrentUser,
    tenant: TenantDep,
) -> list[DocumentTypeRead]:
    async with tenant_context(db, tenant.id):
        result = await db.execute(
            select(DocumentType).where(
                DocumentType.tenant_id == tenant.id,
                DocumentType.is_active.is_(True),
            )
        )
        dts = result.scalars().all()
    return [DocumentTypeRead.model_validate(dt) for dt in dts]


@router.get("/{slug}", response_model=DocumentTypeRead)
async def get_document_type(
    tenant_slug: str,
    slug: str,
    db: DbDep,
    current_user: CurrentUser,
    tenant: TenantDep,
) -> DocumentTypeRead:
    async with tenant_context(db, tenant.id):
        result = await db.execute(
            select(DocumentType).where(
                DocumentType.tenant_id == tenant.id,
                DocumentType.slug == slug,
            )
        )
        dt = result.scalar_one_or_none()
    if not dt:
        raise HTTPException(status_code=404, detail="Document type not found")
    return DocumentTypeRead.model_validate(dt)


@router.patch("/{slug}", response_model=DocumentTypeRead)
async def update_document_type(
    tenant_slug: str,
    slug: str,
    body: DocumentTypeUpdate,
    db: DbDep,
    current_user: CurrentUser,
    tenant: TenantDep,
) -> DocumentTypeRead:
    async with tenant_context(db, tenant.id):
        result = await db.execute(
            select(DocumentType).where(
                DocumentType.tenant_id == tenant.id,
                DocumentType.slug == slug,
            )
        )
        dt = result.scalar_one_or_none()
    if not dt:
        raise HTTPException(status_code=404, detail="Document type not found")

    # Update scalar fields
    for field in ("name", "description", "classification_hints", "extraction_rules", "is_active"):
        value = getattr(body, field, None)
        if value is not None:
            setattr(dt, field, value)

    # Replace fields if provided
    if body.fields is not None:
        await db.execute(
            # cascade delete handles children, but explicit is cleaner
            select(DocumentTypeField).where(DocumentTypeField.document_type_id == dt.id)
        )
        for existing_field in dt.fields:
            await db.delete(existing_field)
        await db.flush()
        for i, f in enumerate(body.fields):
            db.add(DocumentTypeField(
                tenant_id=tenant.id,
                document_type_id=dt.id,
                **{**f.model_dump(), "sort_order": f.sort_order or i},
            ))

    if body.validation_rules is not None:
        for existing_rule in dt.validation_rules:
            await db.delete(existing_rule)
        await db.flush()
        for i, r in enumerate(body.validation_rules):
            db.add(ValidationRule(
                tenant_id=tenant.id,
                document_type_id=dt.id,
                **{**r.model_dump(), "sort_order": r.sort_order or i},
            ))

    await db.commit()
    await db.refresh(dt)
    return DocumentTypeRead.model_validate(dt)


@router.delete("/{slug}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document_type(
    tenant_slug: str,
    slug: str,
    db: DbDep,
    current_user: CurrentUser,
    tenant: TenantDep,
) -> None:
    async with tenant_context(db, tenant.id):
        result = await db.execute(
            select(DocumentType).where(
                DocumentType.tenant_id == tenant.id,
                DocumentType.slug == slug,
            )
        )
        dt = result.scalar_one_or_none()
    if not dt:
        raise HTTPException(status_code=404, detail="Document type not found")
    # Soft delete preserves referential integrity with subdocuments
    dt.is_active = False
    await db.commit()
