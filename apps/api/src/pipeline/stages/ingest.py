# SPDX-License-Identifier: AGPL-3.0-or-later
import io
import uuid
import fitz  # PyMuPDF
from sqlalchemy import select
from ..events import emit_progress
from ...models.document import Document
from ...services.storage_service import StorageService
from ...core.rls import tenant_context


async def run_ingest(ctx: dict, document_id: str, tenant_id: str) -> dict:
    """
    Stage 1: Download PDF, extract page count + raw text, generate thumbnails.
    Returns page_data: {page_num: {text, thumbnail_key}}.
    """
    db = ctx["db"]
    storage = StorageService()
    doc_uuid = uuid.UUID(document_id)
    tenant_uuid = uuid.UUID(tenant_id)

    async with tenant_context(db, tenant_uuid):
        result = await db.execute(
            select(Document).where(Document.id == doc_uuid)
        )
        doc = result.scalar_one()

    # Download PDF bytes
    pdf_bytes = await storage.download(doc.storage_key)

    page_data: dict[int, dict] = {}
    with fitz.open(stream=pdf_bytes, filetype="pdf") as pdf:
        page_count = pdf.page_count
        for page_num in range(page_count):
            page = pdf[page_num]

            # Raw text extraction (native — no OCR yet)
            text = page.get_text("text")

            # Thumbnail generation (72 DPI WebP)
            mat = fitz.Matrix(72 / 72, 72 / 72)
            clip = page.rect
            pix = page.get_pixmap(matrix=mat, clip=clip)
            thumb_bytes = pix.tobytes("webp")

            thumb_key = StorageService.thumbnail_key(tenant_id, document_id, page_num + 1, doc.created_at)
            await storage.upload(thumb_key, thumb_bytes, "image/webp")

            page_data[page_num + 1] = {
                "text": text,
                "thumbnail_key": thumb_key,
                "width": pix.width,
                "height": pix.height,
            }

    # Update document page count
    async with tenant_context(db, tenant_uuid):
        doc.page_count = page_count
        doc.status = "processing"
        await db.flush()

    await emit_progress(
        ctx["redis"], tenant_id, document_id, "ingest", "completed",
        extra={"page_count": page_count},
    )
    return {"page_data": page_data, "page_count": page_count}
