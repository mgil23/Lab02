# SPDX-License-Identifier: AGPL-3.0-or-later
import uuid
from datetime import datetime
from pydantic import BaseModel


class FieldDefinition(BaseModel):
    name: str
    label: str
    field_type: str
    is_required: bool = False
    sort_order: int = 0
    config: dict = {}


class ValidationRuleDefinition(BaseModel):
    field_name: str | None = None
    rule_type: str
    rule_config: dict
    error_message: str
    sort_order: int = 0


class DocumentTypeCreate(BaseModel):
    name: str
    slug: str
    description: str | None = None
    classification_hints: dict = {}
    extraction_rules: dict = {}
    fields: list[FieldDefinition] = []
    validation_rules: list[ValidationRuleDefinition] = []


class DocumentTypeRead(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    tenant_id: uuid.UUID
    name: str
    slug: str
    description: str | None
    classification_hints: dict
    extraction_rules: dict
    is_active: bool
    created_at: datetime
    updated_at: datetime


class DocumentTypeUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    classification_hints: dict | None = None
    extraction_rules: dict | None = None
    fields: list[FieldDefinition] | None = None
    validation_rules: list[ValidationRuleDefinition] | None = None
    is_active: bool | None = None
