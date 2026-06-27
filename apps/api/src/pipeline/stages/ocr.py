# SPDX-License-Identifier: AGPL-3.0-or-later
import uuid
import fitz
import httpx
from sqlalchemy import select
from ...config import settings
from ...models.subdocument import SubDocument
from ...services.storage_service import StorageService
from ...core.rls import tenant_context
from ..events import emit_progress


async def run_ocr(ctx: dict, subdocument_id: str, tenant_id: str) -> dict:
    """
    Stage 4: OCR + PP-Structure for a single subdocument.
    Returns ocr_result: {pages: {page_num: {blocks, tables}}}.
    """
    db = ctx["db"]
    storage = StorageService()
    subdoc_uuid = uuid.UUID(subdocument_id)
    tenant_uuid = uuid.UUID(tenant_id)

    async with tenant_context(db, tenant_uuid):
        result = await db.execute(
            select(SubDocument).where(SubDocument.id == subdoc_uuid)
        )
        subdoc = result.scalar_one()

    pdf_bytes = await storage.download(subdoc.storage_key)

    page_images: list[bytes] = []
    page_native_texts: list[str] = []

    with fitz.open(stream=pdf_bytes, filetype="pdf") as pdf:
        for page_num in range(pdf.page_count):
            page = pdf[page_num]
            page_native_texts.append(page.get_text("text"))
            # Render at 150 DPI for OCR
            mat = fitz.Matrix(150 / 72, 150 / 72)
            pix = page.get_pixmap(matrix=mat)
            page_images.append(pix.tobytes("png"))

    # Send to OCR engine
    async with httpx.AsyncClient(timeout=120.0, base_url=settings.ocr_engine_url) as client:
        response = await client.post(
            "/ocr/pages",
            json={"images_b64": [
                __import__("base64").b64encode(img).decode()
                for img in page_images
            ]},
        )
        response.raise_for_status()
        ocr_pages = response.json()["pages"]

    # Merge OCR results with native text (prefer native when OCR confidence < 0.95)
    pages_result: dict[int, dict] = {}
    for i, ocr_page in enumerate(ocr_pages):
        native_text = page_native_texts[i]
        page_num = i + 1

        # Prefer native text if it's rich enough
        use_native = len(native_text.strip()) > 100
        pages_result[page_num] = {
            "text": native_text if use_native else " ".join(
                b["text"] for b in ocr_page.get("blocks", [])
            ),
            "blocks": ocr_page.get("blocks", []),
            "tables": ocr_page.get("tables", []),
            "source": "native" if use_native else "ocr",
        }

    # Update subdocument OCR status
    async with tenant_context(db, tenant_uuid):
        subdoc.status = "ocr_complete"
        await db.flush()
        await db.commit()

    return {
        "subdocument_id": subdocument_id,
        "pages": pages_result,
    }
