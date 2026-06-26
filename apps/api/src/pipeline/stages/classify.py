# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Multi-signal document boundary detection.
Detects where one sub-document ends and a new one begins within a multi-page PDF.
"""
import hashlib
import re
from dataclasses import dataclass
from ..events import emit_progress

PAGE_RESTART_RE = re.compile(r'\bpage\s*1\s*(of|/)\s*\d+\b', re.IGNORECASE)
ENTITY_WORDS_TO_SKIP = frozenset({"the", "a", "an", "of", "in", "for", "and", "or"})
BOUNDARY_THRESHOLD = 0.55


@dataclass
class PageFeatures:
    page_num: int
    text: str
    layout_hash: str
    primary_entity: str | None
    page_restart_match: bool
    is_blank: bool


def extract_page_features(page_num: int, layout: dict) -> PageFeatures:
    text = layout.get("native_text", "")
    blocks = layout.get("blocks", [])

    # Layout hash: stable fingerprint of block types + rough positions
    block_sig = "|".join(
        f"{b.get('type','?')}:{round(b.get('y', 0) / 50) * 50}"
        for b in blocks[:10]
    )
    layout_hash = hashlib.md5(block_sig.encode()).hexdigest()[:8]  # noqa: S324

    # Primary entity: first heading or large text block
    primary_entity: str | None = None
    for block in blocks:
        if block.get("type") in ("title", "header") and block.get("text"):
            primary_entity = block["text"].strip()[:80]
            break

    is_blank = len(text.strip()) < 30

    return PageFeatures(
        page_num=page_num,
        text=text,
        layout_hash=layout_hash,
        primary_entity=primary_entity,
        page_restart_match=bool(PAGE_RESTART_RE.search(text)),
        is_blank=is_blank,
    )


def detect_boundaries(pages: list[PageFeatures]) -> list[int]:
    """Return list of 1-based page numbers where a new subdocument starts."""
    boundaries = [1]

    for i in range(1, len(pages)):
        prev, curr = pages[i - 1], pages[i]
        score = 0.0
        signals: list[str] = []

        # Hard signals
        if prev.is_blank:
            score += 1.0
            signals.append("blank_separator")

        if curr.page_restart_match:
            score += 0.9
            signals.append("page_restart")

        if (
            prev.primary_entity
            and curr.primary_entity
            and _entity_similarity(prev.primary_entity, curr.primary_entity) < 0.25
        ):
            score += 0.85
            signals.append("entity_change")

        # Soft signals
        if prev.layout_hash != curr.layout_hash:
            score += 0.5
            signals.append("layout_change")

        if score >= BOUNDARY_THRESHOLD:
            boundaries.append(curr.page_num)

    return boundaries


def _entity_similarity(a: str, b: str) -> float:
    a_tokens = {w.lower() for w in a.split() if w.lower() not in ENTITY_WORDS_TO_SKIP}
    b_tokens = {w.lower() for w in b.split() if w.lower() not in ENTITY_WORDS_TO_SKIP}
    if not a_tokens or not b_tokens:
        return 0.0
    return len(a_tokens & b_tokens) / len(a_tokens | b_tokens)


async def run_classify_and_split(
    ctx: dict,
    document_id: str,
    tenant_id: str,
    preprocess_result: dict,
) -> list[dict]:
    """
    Stage 3: Detect document boundaries, create SubDocument records.
    Returns list of subdocument dicts with page ranges.
    """
    layout_data = preprocess_result["layout_data"]
    page_nums = sorted(layout_data.keys())

    pages = [extract_page_features(p, layout_data[p]) for p in page_nums]
    boundaries = detect_boundaries(pages)

    # Group pages into subdocuments
    subdoc_ranges: list[tuple[int, int]] = []
    for i, start in enumerate(boundaries):
        end = boundaries[i + 1] - 1 if i + 1 < len(boundaries) else page_nums[-1]
        subdoc_ranges.append((start, end))

    # Create SubDocument records
    import uuid
    from sqlalchemy import select
    from ...models.subdocument import SubDocument
    from ...models.document import Document
    from ...core.rls import tenant_context
    from ...services.storage_service import StorageService
    from psycopg2.extras import NumericRange
    import fitz

    db = ctx["db"]
    storage = StorageService()
    doc_uuid = uuid.UUID(document_id)
    tenant_uuid = uuid.UUID(tenant_id)

    async with tenant_context(db, tenant_uuid):
        doc_result = await db.execute(
            select(Document).where(Document.id == doc_uuid)
        )
        doc = doc_result.scalar_one()
        pdf_bytes = await storage.download(doc.storage_key)

    subdocuments: list[dict] = []

    with fitz.open(stream=pdf_bytes, filetype="pdf") as src_pdf:
        for start_page, end_page in subdoc_ranges:
            subdoc_id = uuid.uuid4()
            subdoc_key = StorageService.subdocument_key(tenant_id, document_id, str(subdoc_id))

            # Extract subdocument PDF
            subdoc_pdf = fitz.open()
            for p in range(start_page - 1, end_page):
                subdoc_pdf.insert_pdf(src_pdf, from_page=p, to_page=p)
            subdoc_bytes = subdoc_pdf.tobytes()
            subdoc_pdf.close()

            await storage.upload(subdoc_key, subdoc_bytes, "application/pdf")

            # Boundary evidence for explainability
            split_signals = {
                "boundary_page": start_page,
                "page_range": [start_page, end_page],
            }
            if start_page > 1:
                prev_features = pages[start_page - 2]
                curr_features = pages[start_page - 1]
                if curr_features.page_restart_match:
                    split_signals["triggered_by"] = "page_restart"
                elif prev_features.is_blank:
                    split_signals["triggered_by"] = "blank_separator"
                elif prev_features.layout_hash != curr_features.layout_hash:
                    split_signals["triggered_by"] = "layout_change"

            async with tenant_context(db, tenant_uuid):
                from sqlalchemy.dialects.postgresql import Range
                subdoc = SubDocument(
                    id=subdoc_id,
                    tenant_id=tenant_uuid,
                    document_id=doc_uuid,
                    page_range=NumericRange(start_page, end_page + 1),
                    page_count=end_page - start_page + 1,
                    storage_key=subdoc_key,
                    status="pending",
                    split_signals=split_signals,
                )
                db.add(subdoc)
                await db.flush()

            subdocuments.append({
                "id": str(subdoc_id),
                "start_page": start_page,
                "end_page": end_page,
                "page_count": end_page - start_page + 1,
                "storage_key": subdoc_key,
            })

    await db.commit()

    await emit_progress(
        ctx["redis"], tenant_id, document_id, "classify_split", "completed",
        extra={"subdocument_count": len(subdocuments)},
    )
    return subdocuments
