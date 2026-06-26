# SPDX-License-Identifier: AGPL-3.0-or-later
import uuid
from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel


class BoundingBox(BaseModel):
    x: float
    y: float
    width: float
    height: float
    page: int


class ExtractedFieldRead(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    subdocument_id: uuid.UUID
    field_name: str
    field_value: str | None
    confidence: Decimal | None
    page_number: int | None
    bounding_box: dict | None
    source_text: str | None
    reasoning: str | None
    extraction_method: str
    validation_status: str
    validation_errors: dict | None
    human_reviewed: bool
    human_value: str | None
    updated_at: datetime


class ExtractedFieldUpdate(BaseModel):
    human_value: str
    human_reviewed: bool = True


class ExtractionSummary(BaseModel):
    subdocument_id: uuid.UUID
    total_fields: int
    validated: int
    flagged: int
    human_reviewed: int
    fields: list[ExtractedFieldRead]
