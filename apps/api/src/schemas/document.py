# SPDX-License-Identifier: AGPL-3.0-or-later
import uuid
from datetime import datetime
from pydantic import BaseModel


class DocumentRead(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    tenant_id: uuid.UUID
    filename: str
    file_size: int
    page_count: int | None
    status: str
    created_at: datetime
    updated_at: datetime


class DocumentListItem(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    filename: str
    file_size: int
    page_count: int | None
    status: str
    created_at: datetime


class DocumentCreate(BaseModel):
    filename: str


class PipelineStatusResponse(BaseModel):
    document_id: uuid.UUID
    status: str
    stages: dict
    total_duration_ms: int | None
