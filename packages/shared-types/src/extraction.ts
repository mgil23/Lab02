// SPDX-License-Identifier: AGPL-3.0-or-later

export type ValidationStatus =
  | "pending"
  | "valid"
  | "review"
  | "flagged"
  | "human_reviewed";

export interface BoundingBox {
  x: number;
  y: number;
  width: number;
  height: number;
  page: number;
}

export interface ExtractedField {
  id: string;
  subdocument_id: string;
  field_name: string;
  field_value: string | null;
  confidence: number | null;
  page_number: number | null;
  bounding_box: BoundingBox | null;
  source_text: string | null;
  reasoning: string | null;
  extraction_method: "rule" | "llm" | "ocr";
  validation_status: ValidationStatus;
  validation_errors: string[] | null;
  human_reviewed: boolean;
  human_value: string | null;
  updated_at: string;
}

export interface ExtractionSummary {
  subdocument_id: string;
  total_fields: number;
  validated: number;
  flagged: number;
  human_reviewed: number;
  fields: ExtractedField[];
}
