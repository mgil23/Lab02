# SPDX-License-Identifier: AGPL-3.0-or-later
from __future__ import annotations

import math
import uuid
from datetime import datetime
from typing import Generic, Literal, TypeVar

from pydantic import BaseModel, ConfigDict

T = TypeVar("T")


class PaginatedResponse(BaseModel, Generic[T]):
    items: list[T]
    total: int
    page: int
    page_size: int
    pages: int

    @classmethod
    def build(cls, items: list[T], total: int, page: int, page_size: int) -> "PaginatedResponse[T]":
        return cls(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            pages=max(1, math.ceil(total / page_size)) if page_size else 1,
        )


class DocumentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    tenant_id: uuid.UUID
    filename: str
    file_size: int
    page_count: int | None
    status: str
    created_at: datetime
    updated_at: datetime


class DocumentListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    filename: str
    file_size: int
    page_count: int | None
    status: str
    created_at: datetime


class PipelineStatusResponse(BaseModel):
    document_id: uuid.UUID
    status: str
    stages: dict
    total_duration_ms: int | None
    error_message: str | None = None


class KpiResponse(BaseModel):
    total_documents: int
    processing: int
    completed: int
    needs_review: int
    failed: int
    pages_processed_today: int
    avg_processing_ms: int | None


class ChartPoint(BaseModel):
    date: str
    completed: int
    failed: int


class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str


class ChatRequest(BaseModel):
    question: str
    history: list[ChatMessage] = []


class ChatResponse(BaseModel):
    answer: str
