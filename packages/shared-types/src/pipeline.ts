// SPDX-License-Identifier: AGPL-3.0-or-later

export type PipelineEventType =
  | "stage_progress"
  | "field_updated"
  | "stage_complete"
  | "pipeline_failed"
  | "ping";

export interface StageProgressEvent {
  type: "stage_progress";
  stage: string;
  status: "started" | "completed" | "error" | "done";
  timestamp: string;
  error?: string;
  page_count?: number;
  subdocument_count?: number;
  total_ms?: number;
}

export interface FieldUpdatedEvent {
  type: "field_updated";
  subdocument_id: string;
  field_id: string;
  timestamp: string;
}

export interface PipelineFailedEvent {
  type: "pipeline_failed";
  error: string;
  stage: string;
  timestamp: string;
}

export interface PingEvent {
  type: "ping";
}

export type PipelineEvent =
  | StageProgressEvent
  | FieldUpdatedEvent
  | PipelineFailedEvent
  | PingEvent;
