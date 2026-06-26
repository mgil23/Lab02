// SPDX-License-Identifier: AGPL-3.0-or-later
"use client";

import { Plus, Trash2 } from "lucide-react";

const RULE_TYPES = ["regex", "range", "required", "cross_field", "llm_semantic"] as const;
type RuleType = (typeof RULE_TYPES)[number];

export interface ValidationRule {
  id: string;
  field_name: string;
  rule_type: RuleType;
  rule_config: Record<string, string>;
  error_message: string;
}

interface Props {
  rules: ValidationRule[];
  fieldNames: string[];
  onChange: (rules: ValidationRule[]) => void;
}

export function ValidationRuleEditor({ rules, fieldNames, onChange }: Props) {
  function addRule() {
    onChange([
      ...rules,
      {
        id: crypto.randomUUID(),
        field_name: fieldNames[0] ?? "",
        rule_type: "regex",
        rule_config: { pattern: "" },
        error_message: "",
      },
    ]);
  }

  function updateRule(id: string, patch: Partial<ValidationRule>) {
    onChange(rules.map((r) => (r.id === id ? { ...r, ...patch } : r)));
  }

  function removeRule(id: string) {
    onChange(rules.filter((r) => r.id !== id));
  }

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-semibold">Validation Rules</h3>
        <button
          onClick={addRule}
          className="flex items-center gap-1 rounded-md bg-primary px-2.5 py-1.5 text-xs font-medium text-primary-foreground hover:bg-primary/90"
        >
          <Plus className="h-3.5 w-3.5" />
          Add Rule
        </button>
      </div>

      {rules.length === 0 && (
        <p className="rounded-lg border border-dashed p-4 text-center text-sm text-muted-foreground">
          No validation rules. Rules run after extraction.
        </p>
      )}

      <div className="space-y-2">
        {rules.map((rule) => (
          <div key={rule.id} className="rounded-lg border bg-card p-3 space-y-2">
            <div className="grid grid-cols-2 gap-2">
              <div className="space-y-1">
                <label className="text-[10px] font-medium uppercase text-muted-foreground">
                  Field
                </label>
                <select
                  value={rule.field_name}
                  onChange={(e) => updateRule(rule.id, { field_name: e.target.value })}
                  className="w-full rounded border px-2 py-1 text-xs bg-background focus:outline-none focus:ring-1 focus:ring-primary"
                >
                  {fieldNames.map((f) => (
                    <option key={f} value={f}>{f}</option>
                  ))}
                </select>
              </div>
              <div className="space-y-1">
                <label className="text-[10px] font-medium uppercase text-muted-foreground">
                  Rule Type
                </label>
                <select
                  value={rule.rule_type}
                  onChange={(e) => updateRule(rule.id, { rule_type: e.target.value as RuleType })}
                  className="w-full rounded border px-2 py-1 text-xs bg-background focus:outline-none focus:ring-1 focus:ring-primary"
                >
                  {RULE_TYPES.map((t) => (
                    <option key={t} value={t}>{t}</option>
                  ))}
                </select>
              </div>
            </div>
            <div className="space-y-1">
              <label className="text-[10px] font-medium uppercase text-muted-foreground">
                Rule Config (JSON)
              </label>
              <textarea
                value={JSON.stringify(rule.rule_config)}
                onChange={(e) => {
                  try {
                    updateRule(rule.id, { rule_config: JSON.parse(e.target.value) });
                  } catch {}
                }}
                rows={2}
                className="w-full rounded border px-2 py-1 text-xs font-mono focus:outline-none focus:ring-1 focus:ring-primary resize-none"
              />
            </div>
            <div className="flex items-start gap-2">
              <div className="flex-1 space-y-1">
                <label className="text-[10px] font-medium uppercase text-muted-foreground">
                  Error Message
                </label>
                <input
                  value={rule.error_message}
                  onChange={(e) => updateRule(rule.id, { error_message: e.target.value })}
                  placeholder="Value must match pattern XXX-NNNN"
                  className="w-full rounded border px-2 py-1 text-xs focus:outline-none focus:ring-1 focus:ring-primary"
                />
              </div>
              <button
                onClick={() => removeRule(rule.id)}
                className="mt-5 rounded p-1 text-muted-foreground hover:bg-destructive/10 hover:text-destructive"
              >
                <Trash2 className="h-3.5 w-3.5" />
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
