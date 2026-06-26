# SPDX-License-Identifier: AGPL-3.0-or-later
import asyncio
import uuid
from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator
from datetime import datetime, UTC
from opentelemetry import trace
from sqlalchemy import select
from ..models.pipeline_run import PipelineRun
from ..models.document import Document, DocumentStatus
from ..models.usage_record import UsageRecord
from ..core.rls import tenant_context
from ..core.telemetry import PIPELINE_STAGE_DURATION, DOCUMENTS_PROCESSED_TOTAL
from .events import emit_progress
from .stages.ingest import run_ingest
from .stages.preprocess import run_preprocess
from .stages.classify import run_classify_and_split
from .stages.ocr import run_ocr
from .stages.extract import run_extract
import time

tracer = trace.get_tracer("openidp.pipeline")


@asynccontextmanager
async def _stage(
    db: object,
    run: PipelineRun,
    stage_name: str,
) -> AsyncGenerator[None, None]:
    start = time.perf_counter()
    await run.start_stage(db, stage_name)  # type: ignore[arg-type]
    try:
        with tracer.start_as_current_span(f"pipeline.{stage_name}"):
            yield
        await run.complete_stage(db, stage_name)  # type: ignore[arg-type]
    except Exception as e:
        await run.fail_stage(db, stage_name, str(e))  # type: ignore[arg-type]
        raise
    finally:
        duration = time.perf_counter() - start
        PIPELINE_STAGE_DURATION.labels(
            stage=stage_name,
            tenant_id=run.tenant_id,
        ).observe(duration)


async def run_pipeline(ctx: dict, document_id: str, tenant_id: str) -> dict:
    """Main ARQ task: orchestrate all 6 pipeline stages."""
    db = ctx["db"]
    redis = ctx["redis"]
    doc_uuid = uuid.UUID(document_id)
    tenant_uuid = uuid.UUID(tenant_id)

    pipeline_start = time.perf_counter()

    with tracer.start_as_current_span(
        "pipeline.full",
        attributes={"document_id": document_id, "tenant_id": tenant_id},
    ):
        async with tenant_context(db, tenant_uuid):
            run = await PipelineRun.create(db, doc_uuid, tenant_uuid)
            await db.commit()

        try:
            # Stage 1: Ingest + thumbnails
            await emit_progress(redis, tenant_id, document_id, "ingest", "started")
            async with _stage(db, run, "ingest"):
                ingest_result = await run_ingest(ctx, document_id, tenant_id)

            # Stage 2: Preprocess + layout
            await emit_progress(redis, tenant_id, document_id, "preprocess", "started")
            async with _stage(db, run, "preprocess"):
                preprocess_result = await run_preprocess(ctx, document_id, tenant_id, ingest_result)

            # Stage 3: Classify + split
            await emit_progress(redis, tenant_id, document_id, "classify_split", "started")
            async with _stage(db, run, "classify_split"):
                subdocuments = await run_classify_and_split(ctx, document_id, tenant_id, preprocess_result)

            # Stage 4: OCR (parallel across subdocuments)
            await emit_progress(redis, tenant_id, document_id, "ocr", "started")
            async with _stage(db, run, "ocr"):
                ocr_results = await asyncio.gather(*[
                    run_ocr(ctx, s["id"], tenant_id)
                    for s in subdocuments
                ])

            # Stage 5: Strands extraction (parallel)
            await emit_progress(redis, tenant_id, document_id, "extract", "started")
            async with _stage(db, run, "extract"):
                await asyncio.gather(*[
                    run_extract(ctx, s["id"], tenant_id, ocr)
                    for s, ocr in zip(subdocuments, ocr_results)
                ])

            # Stage 6: Finalize
            total_ms = int((time.perf_counter() - pipeline_start) * 1000)
            async with tenant_context(db, tenant_uuid):
                doc_result = await db.execute(select(Document).where(Document.id == doc_uuid))
                doc = doc_result.scalar_one()
                doc.status = DocumentStatus.COMPLETED

                # Record pages processed
                pages_usage = UsageRecord(
                    tenant_id=tenant_uuid,
                    metric="pages_processed",
                    quantity=doc.page_count or 0,
                    metadata_={"document_id": document_id},
                )
                db.add(pages_usage)

                await run.mark_completed(db, total_ms)
                await db.commit()

            DOCUMENTS_PROCESSED_TOTAL.labels(tenant_id=tenant_id, status="completed").inc()
            await emit_progress(
                redis, tenant_id, document_id, "completed", "done",
                extra={"total_ms": total_ms, "subdocument_count": len(subdocuments)},
            )

        except Exception as e:
            async with tenant_context(db, tenant_uuid):
                doc_result = await db.execute(select(Document).where(Document.id == doc_uuid))
                doc = doc_result.scalar_one()
                doc.status = DocumentStatus.FAILED
                await run.mark_failed(db, str(e))
                await db.commit()

            DOCUMENTS_PROCESSED_TOTAL.labels(tenant_id=tenant_id, status="failed").inc()
            await emit_progress(redis, tenant_id, document_id, "failed", "error", error=str(e))
            raise

    return {"run_id": str(run.id), "document_id": document_id}
