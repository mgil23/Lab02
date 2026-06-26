# SPDX-License-Identifier: AGPL-3.0-or-later
import httpx
from ...config import settings
from ..events import emit_progress


async def run_preprocess(
    ctx: dict,
    document_id: str,
    tenant_id: str,
    ingest_result: dict,
) -> dict:
    """
    Stage 2: Call OCR engine for layout analysis (PP-Structure per page).
    Returns layout_data: {page_num: {blocks: [...]}} cached in Redis.
    """
    page_data = ingest_result["page_data"]
    layout_data: dict[int, dict] = {}

    # Batch layout requests to OCR engine
    from ...services.storage_service import StorageService
    storage = StorageService()

    async with httpx.AsyncClient(timeout=60.0, base_url=settings.ocr_engine_url) as client:
        for page_num, pdata in page_data.items():
            # Download the page image for layout analysis
            thumb_bytes = await storage.download(pdata["thumbnail_key"])
            response = await client.post(
                "/structure/layout",
                content=thumb_bytes,
                headers={"Content-Type": "image/webp"},
            )
            response.raise_for_status()
            layout = response.json()
            layout_data[page_num] = {
                **layout,
                "native_text": pdata["text"],
            }

    # Cache layout in Redis for pipeline stages
    import json
    cache_key = f"layout:{document_id}"
    await ctx["redis"].setex(cache_key, 3600, json.dumps(layout_data))

    await emit_progress(
        ctx["redis"], tenant_id, document_id, "preprocess", "completed",
        extra={"pages_analyzed": len(layout_data)},
    )
    return {"layout_data": layout_data}
