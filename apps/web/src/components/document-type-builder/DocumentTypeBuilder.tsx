// SPDX-License-Identifier: AGPL-3.0-or-later
"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Save } from "lucide-react";
import { FieldSchemaEditor, type FieldSchema } from "./FieldSchemaEditor";
import { ValidationRuleEditor, type ValidationRule } from "./ValidationRuleEditor";
import { apiClient } from "@/lib/api";

interface Props {
  tenant: string;
  initial?: {
    id?: string;
    name: string;
    slug: string;
    description?: string;
    fields: FieldSchema[];
    rules: ValidationRule[];
  };
}

export function DocumentTypeBuilder({ tenant, initial }: Props) {
  const router = useRouter();
  const [name, setName] = useState(initial?.name ?? "");
  const [slug, setSlug] = useState(initial?.slug ?? "");
  const [description, setDescription] = useState(initial?.description ?? "");
  const [fields, setFields] = useState<FieldSchema[]>(initial?.fields ?? []);
  const [rules, setRules] = useState<ValidationRule[]>(initial?.rules ?? []);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function save() {
    setSaving(true);
    setError(null);
    try {
      const payload = {
        name,
        slug,
        description,
        fields: fields.map((f, i) => ({ ...f, sort_order: i })),
        validation_rules: rules.map((r, i) => ({ ...r, sort_order: i })),
      };
      if (initial?.id) {
        await apiClient.patch(`/${tenant}/document-types/${initial.slug}`, payload);
      } else {
        await apiClient.post(`/${tenant}/document-types`, payload);
      }
      router.push(`/${tenant}/config/document-types`);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Save failed");
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="space-y-8 max-w-3xl">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div className="space-y-1">
          <h2 className="text-xl font-bold">
            {initial?.id ? "Edit Document Type" : "New Document Type"}
          </h2>
          <p className="text-sm text-muted-foreground">
            Define the fields and validation rules for automatic extraction.
          </p>
        </div>
        <button
          onClick={save}
          disabled={saving || !name || !slug}
          className="flex items-center gap-1.5 rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90 disabled:opacity-50"
        >
          <Save className="h-4 w-4" />
          {saving ? "Saving…" : "Save"}
        </button>
      </div>

      {error && (
        <div className="rounded-md bg-destructive/10 px-4 py-3 text-sm text-destructive">
          {error}
        </div>
      )}

      {/* Basics */}
      <div className="rounded-lg border bg-card p-5 space-y-4">
        <h3 className="font-semibold text-sm">Basic Info</h3>
        <div className="grid grid-cols-2 gap-4">
          <div className="space-y-1.5">
            <label className="text-xs font-medium">Name</label>
            <input
              value={name}
              onChange={(e) => {
                setName(e.target.value);
                if (!initial?.id)
                  setSlug(e.target.value.toLowerCase().replace(/[^a-z0-9]+/g, "-"));
              }}
              placeholder="Invoice"
              className="w-full rounded-md border px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary"
            />
          </div>
          <div className="space-y-1.5">
            <label className="text-xs font-medium">Slug</label>
            <input
              value={slug}
              onChange={(e) => setSlug(e.target.value.toLowerCase().replace(/[^a-z0-9-]/g, ""))}
              placeholder="invoice"
              disabled={!!initial?.id}
              className="w-full rounded-md border px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary disabled:opacity-60"
            />
          </div>
        </div>
        <div className="space-y-1.5">
          <label className="text-xs font-medium">Description</label>
          <textarea
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            placeholder="Standard vendor invoice with line items"
            rows={2}
            className="w-full rounded-md border px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary resize-none"
          />
        </div>
      </div>

      {/* Fields */}
      <div className="rounded-lg border bg-card p-5">
        <FieldSchemaEditor fields={fields} onChange={setFields} />
      </div>

      {/* Validation */}
      <div className="rounded-lg border bg-card p-5">
        <ValidationRuleEditor
          rules={rules}
          fieldNames={fields.map((f) => f.name).filter(Boolean)}
          onChange={setRules}
        />
      </div>
    </div>
  );
}
