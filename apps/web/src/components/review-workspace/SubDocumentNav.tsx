// SPDX-License-Identifier: AGPL-3.0-or-later
"use client";

import type { SubDocument } from "@openidp/shared-types";
import { cn } from "@/lib/utils";

interface Props {
  subDocs: SubDocument[];
  activeId: string | null;
  onSelect: (id: string) => void;
}

export function SubDocumentNav({ subDocs, activeId, onSelect }: Props) {
  if (subDocs.length <= 1) return null;

  return (
    <div className="flex gap-1 border-b bg-muted/30 px-4 py-1.5 overflow-x-auto shrink-0">
      {subDocs.map((s, idx) => (
        <button
          key={s.id}
          onClick={() => onSelect(s.id)}
          className={cn(
            "flex shrink-0 items-center gap-1.5 rounded px-3 py-1.5 text-xs font-medium transition-colors",
            activeId === s.id
              ? "bg-primary text-primary-foreground"
              : "bg-card text-muted-foreground hover:bg-muted hover:text-foreground border"
          )}
        >
          <span>Doc {idx + 1}</span>
          {s.document_type_slug && (
            <span className="rounded bg-white/20 px-1 py-0.5 text-[10px]">
              {s.document_type_slug}
            </span>
          )}
          <span className="opacity-60">
            pp. {s.page_range_start}–{s.page_range_end}
          </span>
        </button>
      ))}
    </div>
  );
}
