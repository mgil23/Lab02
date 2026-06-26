# SPDX-License-Identifier: AGPL-3.0-or-later
import uuid
from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select
from ..dependencies import DbDep, CurrentUser, TenantDep
from ..models.document_type import DocumentType, DocumentTypeField, ValidationRule
from ..schemas.document_type import DocumentTypeCreate, DocumentTypeRead, DocumentTypeUpdate
from ..core.rls import tenant_context

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
        existing = await db.execute(
            select(DocumentType).where(
                DocumentType.tenant_id == tenant.id,
                DocumentType.slug == body.slug,
            )
        )
        if existing.scalar_one_or_none():
            raise HTTPException(status_code=409, detail="Document type slug already exists")

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

        for f in body.fields:
            field = DocumentTypeField(
                tenant_id=tenant.id,
                document_type_id=dt.id,
                **f.model_dump(),
            )
            db.add(field)

        for r in body.validation_rules:
            rule = ValidationRule(
                tenant_id=tenant.id,
                document_type_id=dt.id,
                **r.model_dump(),
            )
            db.add(rule)

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
            select(DocumentType).where(DocumentType.tenant_id == tenant.id)
        )
        dts = result.scalars().all()
    return [DocumentTypeRead.model_validate(dt) for dt in dts]


@router.get("/{dt_id}", response_model=DocumentTypeRead)
async def get_document_type(
    tenant_slug: str,
    dt_id: uuid.UUID,
    db: DbDep,
    current_user: CurrentUser,
    tenant: TenantDep,
) -> DocumentTypeRead:
    async with tenant_context(db, tenant.id):
        result = await db.execute(
            select(DocumentType).where(
                DocumentType.id == dt_id, DocumentType.tenant_id == tenant.id
            )
        )
        dt = result.scalar_one_or_none()
    if not dt:
        raise HTTPException(status_code=404, detail="Document type not found")
    return DocumentTypeRead.model_validate(dt)


@router.patch("/{dt_id}", response_model=DocumentTypeRead)
async def update_document_type(
    tenant_slug: str,
    dt_id: uuid.UUID,
    body: DocumentTypeUpdate,
    db: DbDep,
    current_user: CurrentUser,
    tenant: TenantDep,
) -> DocumentTypeRead:
    async with tenant_context(db, tenant.id):
        result = await db.execute(
            select(DocumentType).where(
                DocumentType.id == dt_id, DocumentType.tenant_id == tenant.id
            )
        )
        dt = result.scalar_one_or_none()
    if not dt:
        raise HTTPException(status_code=404, detail="Document type not found")

    update_data = body.model_dump(exclude_none=True, exclude={"fields", "validation_rules"})
    for k, v in update_data.items():
        setattr(dt, k, v)

    await db.commit()
    await db.refresh(dt)
    return DocumentTypeRead.model_validate(dt)
