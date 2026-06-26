// SPDX-License-Identifier: AGPL-3.0-or-later
"use client";

import { useParams } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import { fetchDocumentType } from "@/lib/api";
import { DocumentTypeBuilder } from "@/components/document-type-builder/DocumentTypeBuilder";

export default function EditDocumentTypePage() {
  const { tenant, slug } = useParams<{ tenant: string; slug: string }>();
  const { data, isLoading } = useQuery({
    queryKey: ["document-type", tenant, slug],
    queryFn: () => fetchDocumentType(tenant, slug),
  });

  if (isLoading || !data) {
    return (
      <div className="p-6">
        <div className="h-8 w-48 animate-pulse rounded bg-muted mb-4" />
        <div className="space-y-4">
          {Array.from({ length: 3 }).map((_, i) => (
            <div key={i} className="h-24 animate-pulse rounded-lg bg-muted" />
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="p-6">
      <DocumentTypeBuilder
        tenant={tenant}
        initial={{
          id: data.id,
          name: data.name,
          slug: data.slug,
          description: data.description,
          fields: (data.fields ?? []).map((f) => ({
            id: f.id,
            name: f.name,
            label: f.label,
            field_type: f.field_type as never,
            is_required: f.is_required,
            sort_order: f.sort_order,
          })),
          rules: [],
        }}
      />
    </div>
  );
}
