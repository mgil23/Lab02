// SPDX-License-Identifier: AGPL-3.0-or-later
"use client";

import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { FileText, ArrowRight } from "lucide-react";
import { fetchDocuments } from "@/lib/api";
import { formatDate, formatBytes } from "@/lib/utils";
import { cn } from "@/lib/utils";

const statusColors: Record<string, string> = {
  pending: "bg-gray-100 text-gray-700",
  processing: "bg-blue-100 text-blue-700",
  completed: "bg-green-100 text-green-700",
  failed: "bg-red-100 text-red-700",
  needs_review: "bg-orange-100 text-orange-700",
};

export function RecentDocuments({ tenant }: { tenant: string }) {
  const { data } = useQuery({
    queryKey: ["documents", tenant, "recent"],
    queryFn: () => fetchDocuments(tenant, { page: 1, page_size: 6 }),
    refetchInterval: 15_000,
  });

  const docs = data?.items ?? [];

  return (
    <div className="rounded-lg border bg-card p-5 space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="font-semibold">Recent Documents</h3>
          <p className="text-xs text-muted-foreground">Latest uploads</p>
        </div>
        <Link
          href={`/${tenant}/documents`}
          className="flex items-center gap-1 text-xs text-primary hover:underline"
        >
          View all <ArrowRight className="h-3 w-3" />
        </Link>
      </div>

      {docs.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-8 text-center text-muted-foreground">
          <FileText className="mb-2 h-8 w-8 opacity-30" />
          <p className="text-sm">No documents yet</p>
        </div>
      ) : (
        <ul className="space-y-2">
          {docs.map((doc) => (
            <li key={doc.id}>
              <Link
                href={`/${tenant}/documents/${doc.id}/review`}
                className="flex items-center gap-3 rounded-md p-2 hover:bg-muted transition-colors"
              >
                <FileText className="h-4 w-4 shrink-0 text-muted-foreground" />
                <div className="min-w-0 flex-1">
                  <p className="truncate text-sm font-medium">{doc.filename}</p>
                  <p className="text-xs text-muted-foreground">
                    {formatBytes(doc.file_size)} · {formatDate(doc.created_at)}
                  </p>
                </div>
                <span
                  className={cn(
                    "shrink-0 rounded-full px-2 py-0.5 text-xs font-medium",
                    statusColors[doc.status] ?? "bg-gray-100 text-gray-700"
                  )}
                >
                  {doc.status.replace("_", " ")}
                </span>
              </Link>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
