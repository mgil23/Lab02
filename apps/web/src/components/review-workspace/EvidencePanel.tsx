// SPDX-License-Identifier: AGPL-3.0-or-later
"use client";

import type { ExtractedField } from "@openidp/shared-types";
import { cn } from "@/lib/utils";

interface Props {
  field: ExtractedField | null;
}

const methodColors: Record<string, string> = {
  llm: "bg-purple-100 text-purple-700",
  rule: "bg-blue-100 text-blue-700",
  ocr: "bg-gray-100 text-gray-700",
};

export function EvidencePanel({ field }: Props) {
  if (!field) {
    return (
      <div className="flex h-44 items-center justify-center border-t text-xs text-muted-foreground">
        Select a field to see evidence
      </div>
    );
  }

  const confidencePct = field.confidence ? Math.round(field.confidence * 100) : null;

  return (
    <div className="border-t bg-muted/20 p-4 space-y-3 overflow-y-auto max-h-52 shrink-0">
      <div className="flex items-center gap-2">
        <span className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
          Evidence
        </span>
        <span
          className={cn(
            "rounded-full px-2 py-0.5 text-[10px] font-medium",
            methodColors[field.extraction_method] ?? "bg-gray-100 text-gray-700"
          )}
        >
          {field.extraction_method}
        </span>
        {confidencePct !== null && (
          <span
            className={cn(
              "rounded-full px-2 py-0.5 text-[10px] font-medium ml-auto",
              confidencePct >= 90
                ? "bg-green-100 text-green-700"
                : confidencePct >= 70
                ? "bg-yellow-100 text-yellow-700"
                : "bg-red-100 text-red-700"
            )}
          >
            {confidencePct}% confidence
          </span>
        )}
      </div>

      {field.source_text && (
        <div className="space-y-1">
          <p className="text-[10px] font-medium uppercase text-muted-foreground">Source Text</p>
          <blockquote className="rounded border-l-2 border-primary pl-2 text-xs italic text-foreground/80">
            {field.source_text}
          </blockquote>
        </div>
      )}

      {field.reasoning && (
        <div className="space-y-1">
          <p className="text-[10px] font-medium uppercase text-muted-foreground">
            AI Reasoning
          </p>
          <p className="text-xs text-foreground/70 leading-relaxed">{field.reasoning}</p>
        </div>
      )}

      {field.validation_errors && Array.isArray(field.validation_errors) && field.validation_errors.length > 0 && (
        <div className="space-y-1">
          <p className="text-[10px] font-medium uppercase text-destructive">Validation Errors</p>
          <ul className="space-y-0.5">
            {(field.validation_errors as string[]).map((err, i) => (
              <li key={i} className="text-xs text-destructive">
                • {err}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
