// SPDX-License-Identifier: AGPL-3.0-or-later
"use client";

import type { PipelineEvent } from "@openidp/shared-types";
import { cn } from "@/lib/utils";
import { Loader2, CheckCircle, XCircle, Wifi, WifiOff } from "lucide-react";

const STAGE_LABELS: Record<string, string> = {
  ingest: "Ingesting document",
  preprocess: "Analyzing layout",
  classify_split: "Classifying & splitting",
  ocr: "Running OCR",
  extract: "Extracting fields",
  persist: "Finalizing",
};

interface Props {
  status: "connecting" | "connected" | "disconnected";
  lastEvent: PipelineEvent | null;
}

export function StatusBanner({ status, lastEvent }: Props) {
  if (status === "disconnected") {
    return (
      <div className="flex h-8 items-center gap-2 border-b bg-muted/50 px-4 text-xs text-muted-foreground">
        <WifiOff className="h-3 w-3" />
        Reconnecting…
      </div>
    );
  }

  if (!lastEvent || lastEvent.type === "ping") {
    return (
      <div className="flex h-8 items-center gap-2 border-b bg-background px-4 text-xs text-muted-foreground">
        <Wifi className="h-3 w-3 text-green-500" />
        {status === "connecting" ? "Connecting…" : "Live"}
      </div>
    );
  }

  if (lastEvent.type === "pipeline_failed") {
    return (
      <div className="flex h-8 items-center gap-2 border-b bg-destructive/10 px-4 text-xs text-destructive">
        <XCircle className="h-3 w-3" />
        Processing failed
        {lastEvent.error && <span className="ml-1 opacity-75">— {lastEvent.error}</span>}
      </div>
    );
  }

  if (lastEvent.type === "stage_complete" && lastEvent.stage === "persist") {
    return (
      <div className="flex h-8 items-center gap-2 border-b bg-green-50 px-4 text-xs text-green-700">
        <CheckCircle className="h-3 w-3" />
        Processing complete
      </div>
    );
  }

  const stageLabel =
    lastEvent.type === "stage_progress" || lastEvent.type === "stage_complete"
      ? STAGE_LABELS[lastEvent.stage] ?? lastEvent.stage
      : null;

  return (
    <div className="flex h-8 items-center gap-2 border-b bg-blue-50 px-4 text-xs text-blue-700">
      <Loader2 className="h-3 w-3 animate-spin" />
      {stageLabel ?? "Processing…"}
    </div>
  );
}
