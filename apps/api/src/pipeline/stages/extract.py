# SPDX-License-Identifier: AGPL-3.0-or-later
import uuid
import json
from datetime import datetime, UTC
from sqlalchemy import select
from ...config import settings
from ...models.subdocument import SubDocument
from ...models.document_type import DocumentType, DocumentTypeField, ValidationRule
from ...models.extracted_field import ExtractedField
from ...models.usage_record import UsageRecord
from ...core.rls import tenant_context
from ..events import emit_progress


async def run_extract(
    ctx: dict,
    subdocument_id: str,
    tenant_id: str,
    ocr_result: dict,
) -> None:
    """
    Stage 5: AWS Strands Agents extraction + validation + persist.
    """
    db = ctx["db"]
    subdoc_uuid = uuid.UUID(subdocument_id)
    tenant_uuid = uuid.UUID(tenant_id)

    async with tenant_context(db, tenant_uuid):
        result = await db.execute(
            select(SubDocument).where(SubDocument.id == subdoc_uuid)
        )
        subdoc = result.scalar_one()

        # Get document type config
        dt_config: dict | None = None
        if subdoc.document_type_id:
            dt_result = await db.execute(
                select(DocumentType).where(DocumentType.id == subdoc.document_type_id)
            )
            dt = dt_result.scalar_one_or_none()
            if dt:
                fields_result = await db.execute(
                    select(DocumentTypeField).where(
                        DocumentTypeField.document_type_id == dt.id
                    ).order_by(DocumentTypeField.sort_order)
                )
                rules_result = await db.execute(
                    select(ValidationRule).where(
                        ValidationRule.document_type_id == dt.id
                    ).order_by(ValidationRule.sort_order)
                )
                dt_config = {
                    "name": dt.name,
                    "fields": [
                        {"name": f.name, "label": f.label, "field_type": f.field_type,
                         "is_required": f.is_required, "config": f.config}
                        for f in fields_result.scalars().all()
                    ],
                    "validation_rules": [
                        {"field_name": r.field_name, "rule_type": r.rule_type,
                         "rule_config": r.rule_config, "error_message": r.error_message}
                        for r in rules_result.scalars().all()
                    ],
                }

    if not dt_config:
        # Fallback: generic extraction
        dt_config = {
            "name": "generic",
            "fields": [],
            "validation_rules": [],
        }

    # Build full text from OCR pages
    pages = ocr_result.get("pages", {})
    full_text = "\n\n".join(
        f"--- PAGE {p} ---\n{pages[p]['text']}" for p in sorted(pages.keys())
    ) if pages else ""
    layout = {"blocks": [
        block
        for p in sorted(pages.keys())
        for block in pages[p].get("blocks", [])
    ]}

    # Run Strands Agents extraction
    try:
        from strands_idp.agent import ExtractionAgent
        agent = ExtractionAgent(dt_config)
        page_range_lower = subdoc.page_range.lower
        page_range_upper = subdoc.page_range.upper
        extraction_result = await agent.run(
            text=full_text,
            layout=layout,
            page_range=(page_range_lower, page_range_upper - 1),
        )
    except ImportError:
        # Fallback without Strands
        extraction_result = _fallback_extract(full_text, dt_config)

    # Run deterministic validation rules
    from ...services.validation_service import ValidationService
    field_values = {
        name: str(data.get("value", "")) if isinstance(data, dict) else None
        for name, data in extraction_result.items()
    }
    validation_results = ValidationService().validate(
        field_values,
        dt_config.get("validation_rules", []),
    )

    # Persist extracted fields
    token_count = 0
    async with tenant_context(db, tenant_uuid):
        for field_name, field_data in extraction_result.items():
            if not isinstance(field_data, dict):
                continue

            vr = validation_results.get(field_name, {"status": "valid", "errors": []})
            llm_status = _determine_validation_status(field_data)
            # Use stricter of LLM-confidence status vs rule-based status
            combined_status = "flagged" if vr["status"] == "flagged" or llm_status == "flagged" else llm_status

            field = ExtractedField(
                tenant_id=tenant_uuid,
                subdocument_id=subdoc_uuid,
                field_name=field_name,
                field_value=str(field_data.get("value", "")) or None,
                confidence=field_data.get("confidence"),
                page_number=field_data.get("page_number"),
                bounding_box=field_data.get("bounding_box"),
                source_text=field_data.get("source_text"),
                reasoning=field_data.get("reasoning"),
                extraction_method="llm",
                validation_status=combined_status,
                validation_errors=vr["errors"] if vr["errors"] else None,
            )
            db.add(field)
            token_count += len(str(field_data.get("source_text", ""))) // 4

        # Record usage
        usage = UsageRecord(
            tenant_id=tenant_uuid,
            metric="llm_tokens",
            quantity=token_count,
            metadata_={"subdocument_id": subdocument_id, "model": settings.bedrock_model_id},
        )
        db.add(usage)

        # Update subdocument status
        subdoc.status = "completed"
        await db.flush()
        await db.commit()


def _determine_validation_status(field_data: dict) -> str:
    confidence = field_data.get("confidence")
    if confidence is None:
        return "pending"
    conf = float(confidence)
    if conf >= settings.extraction_confidence_valid:
        return "valid"
    if conf >= settings.extraction_confidence_review:
        return "review"
    return "flagged"


def _fallback_extract(text: str, dt_config: dict) -> dict:
    """Simple regex-based fallback when Strands Agents are not available."""
    result = {}
    for field in dt_config.get("fields", []):
        result[field["name"]] = {
            "value": None,
            "confidence": 0.0,
            "source_text": None,
            "reasoning": "Fallback extraction — Strands Agents not available",
        }
    return result
