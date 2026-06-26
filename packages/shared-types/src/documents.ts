// SPDX-License-Identifier: AGPL-3.0-or-later

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  pages: number;
}

export type DocumentStatus =
  | "pending"
  | "processing"
  | "completed"
  | "failed"
  | "needs_review";

export interface Document {
  id: string;
  tenant_id: string;
  filename: string;
  file_size: number;
  page_count: number | null;
  status: DocumentStatus;
  created_at: string;
  updated_at: string;
}

export interface DocumentListItem {
  id: string;
  filename: string;
  file_size: number;
  page_count: number | null;
  status: DocumentStatus;
  created_at: string;
}

export interface SubDocument {
  id: string;
  document_id: string;
  document_type_id: string | null;
  document_type_slug: string | null;
  page_count: number;
  page_start: number;
  page_end: number;
  status: string;
  classification_confidence: number | null;
  classification_model: string | null;
  storage_key: string | null;
  split_signals: Record<string, unknown> | null;
  created_at: string;
}

export interface PipelineStatus {
  document_id: string;
  status: string;
  stages: Record<string, StageStatus>;
  total_duration_ms: number | null;
  error_message: string | null;
}

export interface StageStatus {
  started_at?: string;
  ended_at?: string;
  status: "pending" | "running" | "completed" | "failed";
  error?: string;
}

export type DocumentTypeFieldType =
  | "text"
  | "number"
  | "date"
  | "currency"
  | "boolean"
  | "table"
  | "address"
  | "email"
  | "phone";

export interface DocumentTypeField {
  id: string;
  name: string;
  label: string;
  field_type: DocumentTypeFieldType;
  is_required: boolean;
  sort_order: number;
  config: Record<string, unknown>;
}

export interface ValidationRule {
  id: string;
  field_name: string | null;
  rule_type: string;
  rule_config: Record<string, unknown>;
  error_message: string;
  sort_order: number;
}

export interface DocumentType {
  id: string;
  tenant_id: string;
  name: string;
  slug: string;
  description: string | null;
  classification_hints: Record<string, unknown>;
  extraction_rules: Record<string, unknown>;
  is_active: boolean;
  fields: DocumentTypeField[];
  validation_rules: ValidationRule[];
  created_at: string;
  updated_at: string;
}
