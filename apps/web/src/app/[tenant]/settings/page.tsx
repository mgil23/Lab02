// SPDX-License-Identifier: AGPL-3.0-or-later
"use client";

import { useState } from "react";
import { useParams } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import { Key, Webhook, Copy, Plus, Trash2 } from "lucide-react";
import { apiClient } from "@/lib/api";
import { formatDate } from "@/lib/utils";

interface ApiKey {
  id: string;
  name: string;
  key_prefix: string;
  created_at: string;
  last_used_at: string | null;
}

export default function SettingsPage() {
  const { tenant } = useParams<{ tenant: string }>();
  const [tab, setTab] = useState<"api-keys" | "webhooks">("api-keys");

  const { data: apiKeys, refetch } = useQuery<ApiKey[]>({
    queryKey: ["api-keys", tenant],
    queryFn: () => apiClient.get(`/${tenant}/api-keys`),
  });

  const [newKeyName, setNewKeyName] = useState("");
  const [createdKey, setCreatedKey] = useState<string | null>(null);
  const [creating, setCreating] = useState(false);

  async function createKey() {
    if (!newKeyName.trim()) return;
    setCreating(true);
    try {
      const res = await apiClient.post<{ key: string; api_key: ApiKey }>(
        `/${tenant}/api-keys`,
        { name: newKeyName }
      );
      setCreatedKey(res.key);
      setNewKeyName("");
      refetch();
    } finally {
      setCreating(false);
    }
  }

  async function deleteKey(id: string) {
    if (!confirm("Delete this API key? Existing integrations using it will break.")) return;
    await apiClient.delete(`/${tenant}/api-keys/${id}`);
    refetch();
  }

  return (
    <div className="p-6 max-w-3xl space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Settings</h1>
        <p className="text-muted-foreground text-sm">Manage API keys and webhook endpoints.</p>
      </div>

      <div className="flex gap-2">
        {(["api-keys", "webhooks"] as const).map((t) => (
          <button
            key={t}
            onClick={() => setTab(t)}
            className={`rounded-md px-3 py-1.5 text-sm font-medium transition-colors ${
              tab === t
                ? "bg-primary text-primary-foreground"
                : "text-muted-foreground hover:bg-muted"
            }`}
          >
            {t === "api-keys" ? "API Keys" : "Webhooks"}
          </button>
        ))}
      </div>

      {tab === "api-keys" && (
        <div className="space-y-4">
          {createdKey && (
            <div className="rounded-lg border border-green-200 bg-green-50 p-4 space-y-2">
              <p className="text-sm font-medium text-green-800">
                Your new API key — copy it now, it won&apos;t be shown again.
              </p>
              <div className="flex items-center gap-2">
                <code className="flex-1 rounded bg-green-100 px-3 py-1.5 text-xs font-mono break-all">
                  {createdKey}
                </code>
                <button
                  onClick={() => navigator.clipboard.writeText(createdKey)}
                  className="rounded p-1.5 hover:bg-green-100"
                >
                  <Copy className="h-4 w-4 text-green-700" />
                </button>
              </div>
            </div>
          )}

          <div className="flex gap-2">
            <input
              value={newKeyName}
              onChange={(e) => setNewKeyName(e.target.value)}
              placeholder="Key name (e.g., Production Integration)"
              onKeyDown={(e) => e.key === "Enter" && createKey()}
              className="flex-1 rounded-md border px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary"
            />
            <button
              onClick={createKey}
              disabled={!newKeyName.trim() || creating}
              className="flex items-center gap-1.5 rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90 disabled:opacity-50"
            >
              <Plus className="h-4 w-4" />
              Create
            </button>
          </div>

          <div className="rounded-lg border overflow-hidden">
            <table className="w-full text-sm">
              <thead className="bg-muted/50">
                <tr>
                  <th className="px-4 py-2.5 text-left text-xs font-medium text-muted-foreground uppercase tracking-wide">Name</th>
                  <th className="px-4 py-2.5 text-left text-xs font-medium text-muted-foreground uppercase tracking-wide">Prefix</th>
                  <th className="px-4 py-2.5 text-left text-xs font-medium text-muted-foreground uppercase tracking-wide">Created</th>
                  <th className="px-4 py-2.5 text-left text-xs font-medium text-muted-foreground uppercase tracking-wide">Last Used</th>
                  <th />
                </tr>
              </thead>
              <tbody className="divide-y">
                {(apiKeys ?? []).map((k) => (
                  <tr key={k.id}>
                    <td className="px-4 py-3 font-medium">{k.name}</td>
                    <td className="px-4 py-3">
                      <code className="rounded bg-muted px-1.5 py-0.5 text-xs">{k.key_prefix}…</code>
                    </td>
                    <td className="px-4 py-3 text-muted-foreground text-xs">{formatDate(k.created_at)}</td>
                    <td className="px-4 py-3 text-muted-foreground text-xs">
                      {k.last_used_at ? formatDate(k.last_used_at) : "Never"}
                    </td>
                    <td className="px-4 py-3 text-right">
                      <button
                        onClick={() => deleteKey(k.id)}
                        className="rounded p-1 text-muted-foreground hover:text-destructive"
                      >
                        <Trash2 className="h-4 w-4" />
                      </button>
                    </td>
                  </tr>
                ))}
                {(apiKeys ?? []).length === 0 && (
                  <tr>
                    <td colSpan={5} className="px-4 py-8 text-center text-muted-foreground text-sm">
                      No API keys. Create one above.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {tab === "webhooks" && (
        <div className="rounded-lg border border-dashed p-12 text-center text-muted-foreground">
          <Webhook className="mx-auto mb-2 h-8 w-8 opacity-30" />
          <p className="text-sm">Webhook management coming soon.</p>
        </div>
      )}
    </div>
  );
}
