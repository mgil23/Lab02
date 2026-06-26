// SPDX-License-Identifier: AGPL-3.0-or-later
"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import { Plus, Layers, ChevronRight } from "lucide-react";
import { fetchDocumentTypes } from "@/lib/api";

export default function DocumentTypesPage() {
  const { tenant } = useParams<{ tenant: string }>();
  const { data: types, isLoading } = useQuery({
    queryKey: ["document-types", tenant],
    queryFn: () => fetchDocumentTypes(tenant),
  });

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Document Types</h1>
          <p className="text-muted-foreground text-sm">
            Define extraction schemas for your document categories.
          </p>
        </div>
        <Link
          href={`/${tenant}/config/document-types/new`}
          className="flex items-center gap-1.5 rounded-md bg-primary px-3 py-1.5 text-sm font-medium text-primary-foreground hover:bg-primary/90"
        >
          <Plus className="h-4 w-4" />
          New Type
        </Link>
      </div>

      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
        {isLoading
          ? Array.from({ length: 3 }).map((_, i) => (
              <div key={i} className="h-28 animate-pulse rounded-lg border bg-muted" />
            ))
          : (types ?? []).map((dt) => (
              <Link
                key={dt.id}
                href={`/${tenant}/config/document-types/${dt.slug}`}
                className="group rounded-lg border bg-card p-5 hover:border-primary/50 hover:shadow-sm transition-all"
              >
                <div className="flex items-start justify-between">
                  <div className="rounded-full bg-primary/10 p-2">
                    <Layers className="h-4 w-4 text-primary" />
                  </div>
                  <ChevronRight className="h-4 w-4 text-muted-foreground group-hover:text-primary transition-colors" />
                </div>
                <div className="mt-3">
                  <p className="font-semibold">{dt.name}</p>
                  <p className="text-xs text-muted-foreground mt-0.5">{dt.slug}</p>
                  {dt.description && (
                    <p className="text-xs text-muted-foreground mt-1 line-clamp-2">
                      {dt.description}
                    </p>
                  )}
                </div>
              </Link>
            ))}
        {!isLoading && (types ?? []).length === 0 && (
          <div className="col-span-full rounded-lg border border-dashed p-12 text-center text-muted-foreground">
            <Layers className="mx-auto mb-2 h-8 w-8 opacity-30" />
            <p className="text-sm">No document types yet. Create your first schema.</p>
          </div>
        )}
      </div>
    </div>
  );
}
