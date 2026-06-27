# SPDX-License-Identifier: AGPL-3.0-or-later
import uuid
from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel


class SubDocumentRead(BaseModel):
    """Flat response schema — page_start/page_end are extracted from INT4RANGE before serialization."""

    id: uuid.UUID
    document_id: uuid.UUID
    document_type_id: uuid.UUID | None
    document_type_slug: str | None = None
    page_count: int
    page_start: int
    page_end: int
    status: str
    classification_confidence: float | None
    classification_model: str | None
    split_signals: dict | None
    storage_key: str | None
    created_at: datetime
