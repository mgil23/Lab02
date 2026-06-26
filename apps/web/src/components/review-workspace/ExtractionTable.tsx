// SPDX-License-Identifier: AGPL-3.0-or-later
"use client";

import { useState, useCallback } from "react";
import {
  useReactTable,
  getCoreRowModel,
  flexRender,
  createColumnHelper,
  type ColumnDef,
} from "@tanstack/react-table";
import { CheckCircle, AlertCircle, Clock, Pencil, Check, X } from "lucide-react";
import { cn } from "@/lib/utils";
import { patchExtractedField } from "@/lib/api";
import type { ExtractedField } from "@openidp/shared-types";

const colHelper = createColumnHelper<ExtractedField>();

interface Props {
  fields: ExtractedField[];
  selectedFieldId: string | null;
  onFieldSelect: (field: ExtractedField) => void;
  tenant: string;
  subDocumentId: string;
  onSaved: () => void;
}

function ValidationIcon({ status }: { status: string }) {
  if (status === "valid") return <CheckCircle className="h-3.5 w-3.5 text-green-500" />;
  if (status === "invalid") return <AlertCircle className="h-3.5 w-3.5 text-destructive" />;
  return <Clock className="h-3.5 w-3.5 text-muted-foreground" />;
}

function EditableCell({
  field,
  tenant,
  onSaved,
}: {
  field: ExtractedField;
  tenant: string;
  onSaved: () => void;
}) {
  const [editing, setEditing] = useState(false);
  const [value, setValue] = useState(field.human_value ?? field.field_value ?? "");
  const [saving, setSaving] = useState(false);

  const displayed = field.human_value ?? field.field_value ?? "";

  async function save() {
    setSaving(true);
    try {
      await patchExtractedField(tenant, field.id, { human_value: value });
      onSaved();
      setEditing(false);
    } finally {
      setSaving(false);
    }
  }

  if (!editing) {
    return (
      <div className="group flex items-center gap-1">
        <span className={cn("flex-1 truncate text-xs", field.human_value ? "font-medium" : "")}>
          {displayed || <span className="text-muted-foreground italic">—</span>}
        </span>
        <button
          onClick={(e) => { e.stopPropagation(); setEditing(true); }}
          className="invisible rounded p-0.5 hover:bg-muted group-hover:visible"
        >
          <Pencil className="h-3 w-3 text-muted-foreground" />
        </button>
      </div>
    );
  }

  return (
    <div className="flex items-center gap-1" onClick={(e) => e.stopPropagation()}>
      <input
        autoFocus
        value={value}
        onChange={(e) => setValue(e.target.value)}
        onKeyDown={(e) => {
          if (e.key === "Enter") save();
          if (e.key === "Escape") setEditing(false);
        }}
        className="flex-1 rounded border px-1.5 py-0.5 text-xs focus:outline-none focus:ring-1 focus:ring-primary min-w-0"
      />
      <button
        onClick={save}
        disabled={saving}
        className="rounded p-0.5 hover:bg-green-50 text-green-600"
      >
        <Check className="h-3 w-3" />
      </button>
      <button
        onClick={() => setEditing(false)}
        className="rounded p-0.5 hover:bg-muted text-muted-foreground"
      >
        <X className="h-3 w-3" />
      </button>
    </div>
  );
}

export function ExtractionTable({
  fields,
  selectedFieldId,
  onFieldSelect,
  tenant,
  subDocumentId,
  onSaved,
}: Props) {
  const columns: ColumnDef<ExtractedField, unknown>[] = [
    colHelper.accessor("field_name", {
      header: "Field",
      size: 140,
      cell: (info) => (
        <span className="text-xs font-medium">{info.getValue()}</span>
      ),
    }),
    colHelper.display({
      id: "value",
      header: "Value",
      cell: ({ row }) => (
        <EditableCell field={row.original} tenant={tenant} onSaved={onSaved} />
      ),
    }),
    colHelper.accessor("validation_status", {
      header: "",
      size: 28,
      cell: (info) => <ValidationIcon status={info.getValue()} />,
    }),
    colHelper.accessor("confidence", {
      header: "Conf.",
      size: 52,
      cell: (info) => {
        const v = info.getValue();
        return v != null ? (
          <span className="text-xs tabular-nums text-muted-foreground">
            {Math.round(Number(v) * 100)}%
          </span>
        ) : null;
      },
    }),
  ];

  const table = useReactTable({
    data: fields,
    columns,
    getCoreRowModel: getCoreRowModel(),
  });

  return (
    <div className="flex-1 overflow-auto">
      <table className="w-full text-xs border-collapse">
        <thead className="sticky top-0 bg-muted/60 z-10">
          {table.getHeaderGroups().map((hg) => (
            <tr key={hg.id}>
              {hg.headers.map((h) => (
                <th
                  key={h.id}
                  style={{ width: h.column.getSize() }}
                  className="border-b px-3 py-2 text-left text-[10px] font-medium uppercase tracking-wide text-muted-foreground"
                >
                  {flexRender(h.column.columnDef.header, h.getContext())}
                </th>
              ))}
            </tr>
          ))}
        </thead>
        <tbody>
          {table.getRowModel().rows.map((row) => {
            const isSelected = row.original.id === selectedFieldId;
            return (
              <tr
                key={row.id}
                onClick={() => onFieldSelect(row.original)}
                className={cn(
                  "cursor-pointer border-b transition-colors",
                  isSelected ? "bg-primary/8" : "hover:bg-muted/40"
                )}
              >
                {row.getVisibleCells().map((cell) => (
                  <td key={cell.id} className="px-3 py-2 align-middle">
                    {flexRender(cell.column.columnDef.cell, cell.getContext())}
                  </td>
                ))}
              </tr>
            );
          })}
        </tbody>
      </table>
      {fields.length === 0 && (
        <div className="flex h-24 items-center justify-center text-xs text-muted-foreground">
          No fields extracted yet
        </div>
      )}
    </div>
  );
}
