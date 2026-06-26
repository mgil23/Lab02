# SPDX-License-Identifier: AGPL-3.0-or-later
import uuid
from fastapi import APIRouter, HTTPException, UploadFile, File, status
from sqlalchemy import select, func
from ..dependencies import DbDep, CurrentUser, TenantDep
from ..models.document import Document, DocumentStatus
from ..schemas.document import DocumentRead, DocumentListItem, PipelineStatusResponse
from ..services.document_service import DocumentService
from ..services.storage_service import StorageService

router = APIRouter(prefix="/{tenant_slug}/documents", tags=["documents"])
MAX_FILE_SIZE = 100 * 1024 * 1024  # 100 MB


@router.post("", response_model=DocumentRead, status_code=status.HTTP_202_ACCEPTED)
async def upload_document(
    tenant_slug: str,
    file: UploadFile,
    db: DbDep,
    current_user: CurrentUser,
    tenant: TenantDep,
) -> DocumentRead:
    if file.content_type not in ("application/pdf",):
        raise HTTPException(status_code=415, detail="Only PDF files are accepted")

    contents = await file.read()
    if len(contents) > MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail="File too large (max 100 MB)")

    storage = StorageService()
    doc_service = DocumentService(db, storage)
    doc = await doc_service.create_and_enqueue(
        tenant_id=tenant.id,
        filename=file.filename or "document.pdf",
        contents=contents,
        created_by=current_user.id,
    )
    await db.commit()
    return DocumentRead.model_validate(doc)


@router.get("", response_model=list[DocumentListItem])
async def list_documents(
    tenant_slug: str,
    db: DbDep,
    current_user: CurrentUser,
    tenant: TenantDep,
    status: str | None = None,
    offset: int = 0,
    limit: int = 50,
) -> list[DocumentListItem]:
    from ..core.rls import tenant_context
    async with tenant_context(db, tenant.id):
        query = select(Document).where(Document.tenant_id == tenant.id)
        if status:
            query = query.where(Document.status == status)
        query = query.order_by(Document.created_at.desc()).offset(offset).limit(min(limit, 200))
        result = await db.execute(query)
        docs = result.scalars().all()
    return [DocumentListItem.model_validate(d) for d in docs]


@router.get("/{document_id}", response_model=DocumentRead)
async def get_document(
    tenant_slug: str,
    document_id: uuid.UUID,
    db: DbDep,
    current_user: CurrentUser,
    tenant: TenantDep,
) -> DocumentRead:
    from ..core.rls import tenant_context
    async with tenant_context(db, tenant.id):
        result = await db.execute(
            select(Document).where(
                Document.id == document_id,
                Document.tenant_id == tenant.id,
            )
        )
        doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return DocumentRead.model_validate(doc)


@router.get("/{document_id}/status", response_model=PipelineStatusResponse)
async def get_pipeline_status(
    tenant_slug: str,
    document_id: uuid.UUID,
    db: DbDep,
    current_user: CurrentUser,
    tenant: TenantDep,
) -> PipelineStatusResponse:
    from ..core.rls import tenant_context
    from ..models.pipeline_run import PipelineRun
    async with tenant_context(db, tenant.id):
        result = await db.execute(
            select(PipelineRun)
            .where(PipelineRun.document_id == document_id)
            .order_by(PipelineRun.created_at.desc())
            .limit(1)
        )
        run = result.scalar_one_or_none()
    if not run:
        raise HTTPException(status_code=404, detail="Pipeline run not found")
    return PipelineStatusResponse(
        document_id=document_id,
        status=run.status,
        stages=run.stages,
        total_duration_ms=run.total_duration_ms,
    )


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    tenant_slug: str,
    document_id: uuid.UUID,
    db: DbDep,
    current_user: CurrentUser,
    tenant: TenantDep,
) -> None:
    from ..core.rls import tenant_context
    async with tenant_context(db, tenant.id):
        result = await db.execute(
            select(Document).where(
                Document.id == document_id,
                Document.tenant_id == tenant.id,
            )
        )
        doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    await db.delete(doc)
    await db.commit()
