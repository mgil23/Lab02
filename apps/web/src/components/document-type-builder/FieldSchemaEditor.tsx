// SPDX-License-Identifier: AGPL-3.0-or-later
"use client";

import { useState } from "react";
import { Plus, Trash2, GripVertical } from "lucide-react";
import { cn } from "@/lib/utils";

const FIELD_TYPES = [
  "text", "number", "date", "currency", "boolean", "table", "address",
] as const;
type FieldType = (typeof FIELD_TYPES)[number];

export interface FieldSchema {
  id: string;
  name: string;
  label: string;
  field_type: FieldType;
  is_required: boolean;
  sort_order: number;
}

interface Props {
  fields: FieldSchema[];
  onChange: (fields: FieldSchema[]) => void;
}

export function FieldSchemaEditor({ fields, onChange }: Props) {
  function addField() {
    onChange([
      ...fields,
      {
        id: crypto.randomUUID(),
        name: "",
        label: "",
        field_type: "text",
        is_required: false,
        sort_order: fields.length,
      },
    ]);
  }

  function updateField(id: string, patch: Partial<FieldSchema>) {
    onChange(fields.map((f) => (f.id === id ? { ...f, ...patch } : f)));
  }

  function removeField(id: string) {
    onChange(fields.filter((f) => f.id !== id));
  }

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-semibold">Fields</h3>
        <button
          onClick={addField}
          className="flex items-center gap-1 rounded-md bg-primary px-2.5 py-1.5 text-xs font-medium text-primary-foreground hover:bg-primary/90"
        >
          <Plus className="h-3.5 w-3.5" />
          Add Field
        </button>
      </div>

      {fields.length === 0 && (
        <p className="rounded-lg border border-dashed p-6 text-center text-sm text-muted-foreground">
          No fields defined. Add a field to start building your schema.
        </p>
      )}

      <div className="space-y-2">
        {fields.map((field) => (
          <div
            key={field.id}
            className="flex items-start gap-2 rounded-lg border bg-card p-3"
          >
            <GripVertical className="mt-2 h-4 w-4 shrink-0 text-muted-foreground/40 cursor-grab" />
            <div className="flex-1 grid grid-cols-2 gap-2">
              <div className="space-y-1">
                <label className="text-[10px] font-medium uppercase text-muted-foreground">
                  Field Name
                </label>
                <input
                  value={field.name}
                  onChange={(e) =>
                    updateField(field.id, {
                      name: e.target.value.toLowerCase().replace(/\s+/g, "_"),
                      label: field.label || e.target.value,
                    })
                  }
                  placeholder="invoice_number"
                  className="w-full rounded border px-2 py-1 text-xs focus:outline-none focus:ring-1 focus:ring-primary"
                />
              </div>
              <div className="space-y-1">
                <label className="text-[10px] font-medium uppercase text-muted-foreground">
                  Display Label
                </label>
                <input
                  value={field.label}
                  onChange={(e) => updateField(field.id, { label: e.target.value })}
                  placeholder="Invoice Number"
                  className="w-full rounded border px-2 py-1 text-xs focus:outline-none focus:ring-1 focus:ring-primary"
                />
              </div>
              <div className="space-y-1">
                <label className="text-[10px] font-medium uppercase text-muted-foreground">
                  Type
                </label>
                <select
                  value={field.field_type}
                  onChange={(e) =>
                    updateField(field.id, { field_type: e.target.value as FieldType })
                  }
                  className="w-full rounded border px-2 py-1 text-xs focus:outline-none focus:ring-1 focus:ring-primary bg-background"
                >
                  {FIELD_TYPES.map((t) => (
                    <option key={t} value={t}>
                      {t}
                    </option>
                  ))}
                </select>
              </div>
              <div className="flex items-end gap-2">
                <label className="flex items-center gap-1.5 text-xs cursor-pointer">
                  <input
                    type="checkbox"
                    checked={field.is_required}
                    onChange={(e) => updateField(field.id, { is_required: e.target.checked })}
                    className="rounded"
                  />
                  Required
                </label>
              </div>
            </div>
            <button
              onClick={() => removeField(field.id)}
              className="mt-1 rounded p-1 text-muted-foreground hover:bg-destructive/10 hover:text-destructive"
            >
              <Trash2 className="h-3.5 w-3.5" />
            </button>
          </div>
        ))}
      </div>
    </div>
  );
}
