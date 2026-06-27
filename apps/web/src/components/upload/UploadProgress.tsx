// SPDX-License-Identifier: AGPL-3.0-or-later
"use client";

import { CheckCircle, XCircle, Loader2 } from "lucide-react";
import { cn } from "@/lib/utils";

export type UploadItem = {
  id: string;
  filename: string;
  progress: number;
  status: "uploading" | "done" | "error";
  error?: string;
};

export function UploadProgress({ items }: { items: UploadItem[] }) {
  if (items.length === 0) return null;

  return (
    <div className="space-y-2">
      {items.map((item) => (
        <div key={item.id} className="rounded-lg border bg-card p-3">
          <div className="flex items-center gap-3">
            {item.status === "uploading" && (
              <Loader2 className="h-4 w-4 shrink-0 animate-spin text-primary" />
            )}
            {item.status === "done" && (
              <CheckCircle className="h-4 w-4 shrink-0 text-green-500" />
            )}
            {item.status === "error" && (
              <XCircle className="h-4 w-4 shrink-0 text-destructive" />
            )}
            <div className="min-w-0 flex-1">
              <p className="truncate text-sm font-medium">{item.filename}</p>
              {item.error && (
                <p className="text-xs text-destructive">{item.error}</p>
              )}
            </div>
            {item.status === "uploading" && (
              <span className="shrink-0 text-xs text-muted-foreground tabular-nums">
                {item.progress}%
              </span>
            )}
          </div>
          {item.status === "uploading" && (
            <div className="mt-2 h-1 overflow-hidden rounded-full bg-muted">
              <div
                className="h-full rounded-full bg-primary transition-all duration-200"
                style={{ width: `${item.progress}%` }}
              />
            </div>
          )}
        </div>
      ))}
    </div>
  );
}
