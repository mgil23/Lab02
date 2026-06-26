# SPDX-License-Identifier: AGPL-3.0-or-later
import uuid
from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel


class SubDocumentRead(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    document_id: uuid.UUID
    document_type_id: uuid.UUID | None
    page_count: int
    status: str
    classification_confidence: Decimal | None
    classification_model: str | None
    split_signals: dict | None
    storage_key: str | None
    created_at: datetime

    @property
    def page_start(self) -> int:
        return self.page_range.lower  # type: ignore[attr-defined]

    @property
    def page_end(self) -> int:
        return self.page_range.upper  # type: ignore[attr-defined]
