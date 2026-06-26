# SPDX-License-Identifier: AGPL-3.0-or-later
from __future__ import annotations

import uuid
from datetime import date, datetime, timedelta, UTC

from fastapi import APIRouter, HTTPException, UploadFile, status
from sqlalchemy import func, select

from ..core.rls import tenant_context
from ..dependencies import CurrentUser, DbDep, TenantDep
from ..models.document import Document
from ..models.pipeline_run import PipelineRun
from ..models.usage_record import UsageRecord
from ..schemas.document import (
    ChatRequest,
    ChatResponse,
    ChartPoint,
    DocumentListItem,
    DocumentRead,
    KpiResponse,
    PaginatedResponse,
    PipelineStatusResponse,
)
from ..services.document_service import DocumentService
from ..services.storage_service import StorageService

from ..config import settings as _cfg

router = APIRouter(prefix="/{tenant_slug}/documents", tags=["documents"])

_MAX_PAGE_SIZE = 100


def _max_file_bytes() -> int:
    return _cfg.pipeline_max_file_size_mb * 1024 * 1024


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
    max_bytes = _max_file_bytes()
    if len(contents) > max_bytes:
        raise HTTPException(
            status_code=413,
            detail=f"File too large (max {_cfg.pipeline_max_file_size_mb} MB)",
        )

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


@router.get("", response_model=PaginatedResponse[DocumentListItem])
async def list_documents(
    tenant_slug: str,
    db: DbDep,
    current_user: CurrentUser,
    tenant: TenantDep,
    status_filter: str | None = None,
    page: int = 1,
    page_size: int = 20,
) -> PaginatedResponse[DocumentListItem]:
    page = max(1, page)
    page_size = min(max(1, page_size), _MAX_PAGE_SIZE)
    offset = (page - 1) * page_size

    async with tenant_context(db, tenant.id):
        base_q = select(Document).where(Document.tenant_id == tenant.id)
        if status_filter:
            base_q = base_q.where(Document.status == status_filter)

        total_result = await db.execute(
            select(func.count()).select_from(base_q.subquery())
        )
        total = total_result.scalar_one()

        items_result = await db.execute(
            base_q.order_by(Document.created_at.desc()).offset(offset).limit(page_size)
        )
        docs = items_result.scalars().all()

    return PaginatedResponse.build(
        items=[DocumentListItem.model_validate(d) for d in docs],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/kpi", response_model=KpiResponse)
async def get_kpi(
    tenant_slug: str,
    db: DbDep,
    current_user: CurrentUser,
    tenant: TenantDep,
) -> KpiResponse:
    async with tenant_context(db, tenant.id):
        counts = await db.execute(
            select(Document.status, func.count(Document.id))
            .where(Document.tenant_id == tenant.id)
            .group_by(Document.status)
        )
        status_map: dict[str, int] = {row[0]: row[1] for row in counts.all()}

        today_start = datetime.now(UTC).replace(hour=0, minute=0, second=0, microsecond=0)
        pages_today_result = await db.execute(
            select(func.coalesce(func.sum(UsageRecord.quantity), 0))
            .where(
                UsageRecord.tenant_id == tenant.id,
                UsageRecord.metric == "pages_processed",
                UsageRecord.recorded_at >= today_start,
            )
        )
        pages_today = int(pages_today_result.scalar_one())

        avg_ms_result = await db.execute(
            select(func.avg(PipelineRun.total_duration_ms))
            .where(
                PipelineRun.tenant_id == tenant.id,
                PipelineRun.status == "completed",
                PipelineRun.total_duration_ms.isnot(None),
            )
        )
        avg_ms_raw = avg_ms_result.scalar_one()

    total = sum(status_map.values())
    return KpiResponse(
        total_documents=total,
        processing=status_map.get("processing", 0),
        completed=status_map.get("completed", 0),
        needs_review=status_map.get("needs_review", 0),
        failed=status_map.get("failed", 0),
        pages_processed_today=pages_today,
        avg_processing_ms=int(avg_ms_raw) if avg_ms_raw else None,
    )


@router.get("/chart", response_model=list[ChartPoint])
async def get_chart(
    tenant_slug: str,
    db: DbDep,
    current_user: CurrentUser,
    tenant: TenantDep,
    days: int = 7,
) -> list[ChartPoint]:
    days = min(max(1, days), 90)
    cutoff = datetime.now(UTC) - timedelta(days=days)

    async with tenant_context(db, tenant.id):
        result = await db.execute(
            select(
                func.date_trunc("day", PipelineRun.created_at).label("day"),
                func.count().filter(PipelineRun.status == "completed").label("completed"),
                func.count().filter(PipelineRun.status == "failed").label("failed"),
            )
            .where(
                PipelineRun.tenant_id == tenant.id,
                PipelineRun.created_at >= cutoff,
            )
            .group_by("day")
            .order_by("day")
        )
        rows = result.all()

    # Fill gaps with zeros
    day_map: dict[str, tuple[int, int]] = {
        str(r.day.date()): (r.completed, r.failed) for r in rows
    }
    points: list[ChartPoint] = []
    for i in range(days):
        d = (cutoff + timedelta(days=i + 1)).date()
        key = str(d)
        completed, failed = day_map.get(key, (0, 0))
        points.append(ChartPoint(date=key, completed=completed, failed=failed))

    return points


@router.get("/{document_id}", response_model=DocumentRead)
async def get_document(
    tenant_slug: str,
    document_id: uuid.UUID,
    db: DbDep,
    current_user: CurrentUser,
    tenant: TenantDep,
) -> DocumentRead:
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


@router.get("/{document_id}/pipeline-status", response_model=PipelineStatusResponse)
async def get_pipeline_status(
    tenant_slug: str,
    document_id: uuid.UUID,
    db: DbDep,
    current_user: CurrentUser,
    tenant: TenantDep,
) -> PipelineStatusResponse:
    async with tenant_context(db, tenant.id):
        result = await db.execute(
            select(PipelineRun)
            .where(
                PipelineRun.document_id == document_id,
                PipelineRun.tenant_id == tenant.id,
            )
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
        error_message=run.error_message,
    )


@router.post("/{document_id}/chat", response_model=ChatResponse)
async def chat_with_document(
    tenant_slug: str,
    document_id: uuid.UUID,
    body: ChatRequest,
    db: DbDep,
    current_user: CurrentUser,
    tenant: TenantDep,
) -> ChatResponse:
    """Chat with a document using its extracted text as context."""
    from ..models.subdocument import SubDocument
    from ..models.extracted_field import ExtractedField

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

    # Build context from extracted fields
    async with tenant_context(db, tenant.id):
        subdoc_result = await db.execute(
            select(SubDocument).where(SubDocument.document_id == document_id)
        )
        subdocs = subdoc_result.scalars().all()

        context_parts: list[str] = [f"Document: {doc.filename}"]
        for subdoc in subdocs:
            fields_result = await db.execute(
                select(ExtractedField).where(ExtractedField.subdocument_id == subdoc.id)
            )
            fields = fields_result.scalars().all()
            if fields:
                context_parts.append(f"\nSubdocument (pages {subdoc.page_range.lower}-{subdoc.page_range.upper}):")
                for f in fields:
                    value = f.human_value or f.field_value or "N/A"
                    context_parts.append(f"  {f.field_name}: {value}")

    document_context = "\n".join(context_parts)

    # Use Strands Agent for chat
    try:
        from strands import Agent
        from strands.models import BedrockModel
        from ..config import settings

        try:
            from pii_sanitizer.sanitizer import PiiSanitizer
            _pii = PiiSanitizer()
            sanitized_context, ctx_token_map = _pii.sanitize(document_context)
            sanitized_question, q_token_map = _pii.sanitize(body.question)
            token_map = {**ctx_token_map, **q_token_map}
        except Exception:
            sanitized_context = document_context
            sanitized_question = body.question
            token_map = {}

        history_text = "\n".join(
            f"{m.role.upper()}: {m.content}" for m in body.history[-6:]
        )
        prompt = (
            f"You are an assistant helping review an extracted document.\n\n"
            f"DOCUMENT CONTEXT:\n{sanitized_context}\n\n"
            f"{'CONVERSATION HISTORY:\\n' + history_text + chr(10) + chr(10) if history_text else ''}"
            f"USER QUESTION: {sanitized_question}\n\n"
            f"Answer based on the document context. Be concise and accurate."
        )

        agent = Agent(
            model=BedrockModel(
                model_id=settings.bedrock_model_id,
                region_name=settings.aws_default_region,
                temperature=0.3,
                max_tokens=1024,
            ),
        )
        raw = await agent.run_async(prompt)
        raw_answer = str(raw) if raw else "I couldn't find an answer in this document."

        # Restore PII tokens in the answer
        if token_map:
            answer = _pii.restore(raw_answer, token_map)  # type: ignore[arg-type]
        else:
            answer = raw_answer

    except Exception:
        # Graceful fallback when Strands/Bedrock unavailable
        answer = (
            f"I found the following information in '{doc.filename}':\n"
            + document_context[len(f"Document: {doc.filename}"):]
        )

    return ChatResponse(answer=answer)


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    tenant_slug: str,
    document_id: uuid.UUID,
    db: DbDep,
    current_user: CurrentUser,
    tenant: TenantDep,
) -> None:
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
