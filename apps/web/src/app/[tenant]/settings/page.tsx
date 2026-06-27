// SPDX-License-Identifier: AGPL-3.0-or-later
"use client";

import { useState } from "react";
import { useParams } from "next/navigation";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  Key,
  Webhook,
  Copy,
  Plus,
  Trash2,
  Shield,
  Sliders,
  Zap,
  CheckCircle,
  XCircle,
  RotateCcw,
  Eye,
  EyeOff,
} from "lucide-react";
import {
  apiClient,
  fetchWebhooks,
  createWebhook,
  deleteWebhook,
  toggleWebhook,
  fetchPlatformSettings,
  updatePlatformSettings,
  resetPlatformSettings,
  type PlatformSettings,
  type WebhookRecord,
  type WebhookCreateResponse,
} from "@/lib/api";
import { formatDate } from "@/lib/utils";

type Tab = "api-keys" | "webhooks" | "pii" | "extraction" | "pipeline";

interface ApiKey {
  id: string;
  name: string;
  key_prefix: string;
  created_at: string;
  last_used_at: string | null;
}

const WEBHOOK_EVENTS = [
  { value: "document.completed", label: "Document Completed" },
  { value: "document.failed", label: "Document Failed" },
  { value: "document.needs_review", label: "Needs Review" },
  { value: "extraction.field_updated", label: "Field Updated" },
];

export default function SettingsPage() {
  const { tenant } = useParams<{ tenant: string }>();
  const qc = useQueryClient();
  const [tab, setTab] = useState<Tab>("api-keys");

  const tabs: { key: Tab; label: string; icon: React.ReactNode }[] = [
    { key: "api-keys", label: "API Keys", icon: <Key className="h-4 w-4" /> },
    { key: "webhooks", label: "Webhooks", icon: <Webhook className="h-4 w-4" /> },
    { key: "pii", label: "PII / Privacy", icon: <Shield className="h-4 w-4" /> },
    { key: "extraction", label: "Extraction", icon: <Sliders className="h-4 w-4" /> },
    { key: "pipeline", label: "Pipeline", icon: <Zap className="h-4 w-4" /> },
  ];

  return (
    <div className="p-6 max-w-4xl space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Settings</h1>
        <p className="text-muted-foreground text-sm">
          Manage API keys, webhooks, and platform configuration for this workspace.
        </p>
      </div>

      <div className="flex flex-wrap gap-1.5 border-b pb-2">
        {tabs.map((t) => (
          <button
            key={t.key}
            onClick={() => setTab(t.key)}
            className={`flex items-center gap-1.5 rounded-md px-3 py-1.5 text-sm font-medium transition-colors ${
              tab === t.key
                ? "bg-primary text-primary-foreground"
                : "text-muted-foreground hover:bg-muted"
            }`}
          >
            {t.icon}
            {t.label}
          </button>
        ))}
      </div>

      {tab === "api-keys" && <ApiKeysTab tenant={tenant} qc={qc} />}
      {tab === "webhooks" && <WebhooksTab tenant={tenant} qc={qc} />}
      {tab === "pii" && <PiiTab tenant={tenant} qc={qc} />}
      {tab === "extraction" && <ExtractionTab tenant={tenant} qc={qc} />}
      {tab === "pipeline" && <PipelineTab tenant={tenant} qc={qc} />}
    </div>
  );
}

// ── API Keys Tab ──────────────────────────────────────────────────────────────

function ApiKeysTab({ tenant, qc }: { tenant: string; qc: ReturnType<typeof useQueryClient> }) {
  const { data: apiKeys, refetch } = useQuery<ApiKey[]>({
    queryKey: ["api-keys", tenant],
    queryFn: () => apiClient.get(`/${tenant}/api-keys`),
  });

  const [newKeyName, setNewKeyName] = useState("");
  const [createdKey, setCreatedKey] = useState<string | null>(null);
  const [creating, setCreating] = useState(false);
  const [copied, setCopied] = useState(false);

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

  async function copyKey(key: string) {
    await navigator.clipboard.writeText(key);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  }

  async function deleteKey(id: string) {
    if (!confirm("Delete this API key? Existing integrations using it will break.")) return;
    await apiClient.delete(`/${tenant}/api-keys/${id}`);
    refetch();
  }

  return (
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
              onClick={() => copyKey(createdKey)}
              className="rounded p-1.5 hover:bg-green-100"
            >
              {copied ? (
                <CheckCircle className="h-4 w-4 text-green-600" />
              ) : (
                <Copy className="h-4 w-4 text-green-700" />
              )}
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

      <p className="text-xs text-muted-foreground">
        Use API keys with the header <code className="bg-muted px-1 rounded">Authorization: Bearer &lt;key&gt;</code>.
        Keys start with <code className="bg-muted px-1 rounded">oidp_</code> and are never retrievable after creation.
      </p>
    </div>
  );
}

// ── Webhooks Tab ──────────────────────────────────────────────────────────────

function WebhooksTab({ tenant, qc }: { tenant: string; qc: ReturnType<typeof useQueryClient> }) {
  const { data: webhooks, refetch } = useQuery<WebhookRecord[]>({
    queryKey: ["webhooks", tenant],
    queryFn: () => fetchWebhooks(tenant),
  });

  const [url, setUrl] = useState("");
  const [selectedEvents, setSelectedEvents] = useState<string[]>([]);
  const [creating, setCreating] = useState(false);
  const [newSecret, setNewSecret] = useState<string | null>(null);
  const [showSecret, setShowSecret] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);

  function toggleEvent(event: string) {
    setSelectedEvents((prev) =>
      prev.includes(event) ? prev.filter((e) => e !== event) : [...prev, event]
    );
  }

  async function addWebhook() {
    setFormError(null);
    if (!url.trim()) { setFormError("URL is required"); return; }
    if (selectedEvents.length === 0) { setFormError("Select at least one event"); return; }
    setCreating(true);
    try {
      const res = await createWebhook(tenant, { url: url.trim(), events: selectedEvents });
      setNewSecret(res.secret);
      setShowSecret(true);
      setUrl("");
      setSelectedEvents([]);
      refetch();
    } catch (e: unknown) {
      setFormError(e instanceof Error ? e.message : "Failed to create webhook");
    } finally {
      setCreating(false);
    }
  }

  async function handleDelete(id: string) {
    if (!confirm("Delete this webhook? No more events will be delivered to this endpoint.")) return;
    await deleteWebhook(tenant, id);
    refetch();
  }

  async function handleToggle(id: string, current: boolean) {
    await toggleWebhook(tenant, id, !current);
    refetch();
  }

  return (
    <div className="space-y-5">
      {newSecret && (
        <div className="rounded-lg border border-amber-200 bg-amber-50 p-4 space-y-2">
          <p className="text-sm font-medium text-amber-800">
            Webhook created — save your signing secret now. It won&apos;t be shown again.
          </p>
          <p className="text-xs text-amber-700">
            Verify the <code className="bg-amber-100 px-1 rounded">X-OpenIDP-Signature</code> header using this secret to authenticate incoming events.
          </p>
          <div className="flex items-center gap-2">
            <code className="flex-1 rounded bg-amber-100 px-3 py-1.5 text-xs font-mono break-all">
              {showSecret ? newSecret : "whsec_••••••••••••••••"}
            </code>
            <button onClick={() => setShowSecret((s) => !s)} className="rounded p-1.5 hover:bg-amber-100">
              {showSecret ? <EyeOff className="h-4 w-4 text-amber-700" /> : <Eye className="h-4 w-4 text-amber-700" />}
            </button>
            <button
              onClick={() => { navigator.clipboard.writeText(newSecret); }}
              className="rounded p-1.5 hover:bg-amber-100"
            >
              <Copy className="h-4 w-4 text-amber-700" />
            </button>
            <button onClick={() => setNewSecret(null)} className="rounded p-1.5 hover:bg-amber-100">
              <XCircle className="h-4 w-4 text-amber-600" />
            </button>
          </div>
        </div>
      )}

      <div className="rounded-lg border p-4 space-y-3">
        <h3 className="text-sm font-semibold">Add Webhook Endpoint</h3>
        <div>
          <label className="text-xs font-medium text-muted-foreground">Endpoint URL</label>
          <input
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            placeholder="https://your-app.com/webhooks/openidp"
            className="mt-1 w-full rounded-md border px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary"
          />
        </div>
        <div>
          <label className="text-xs font-medium text-muted-foreground">Events to subscribe</label>
          <div className="mt-1.5 flex flex-wrap gap-2">
            {WEBHOOK_EVENTS.map((ev) => (
              <button
                key={ev.value}
                type="button"
                onClick={() => toggleEvent(ev.value)}
                className={`rounded-full border px-3 py-1 text-xs font-medium transition-colors ${
                  selectedEvents.includes(ev.value)
                    ? "border-primary bg-primary/10 text-primary"
                    : "border-border text-muted-foreground hover:border-primary/50"
                }`}
              >
                {ev.label}
              </button>
            ))}
          </div>
        </div>
        {formError && <p className="text-xs text-destructive">{formError}</p>}
        <button
          onClick={addWebhook}
          disabled={creating}
          className="flex items-center gap-1.5 rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90 disabled:opacity-50"
        >
          <Plus className="h-4 w-4" />
          {creating ? "Creating…" : "Add Webhook"}
        </button>
      </div>

      <div className="rounded-lg border overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-muted/50">
            <tr>
              <th className="px-4 py-2.5 text-left text-xs font-medium text-muted-foreground uppercase tracking-wide">URL</th>
              <th className="px-4 py-2.5 text-left text-xs font-medium text-muted-foreground uppercase tracking-wide">Events</th>
              <th className="px-4 py-2.5 text-left text-xs font-medium text-muted-foreground uppercase tracking-wide">Status</th>
              <th className="px-4 py-2.5 text-left text-xs font-medium text-muted-foreground uppercase tracking-wide">Created</th>
              <th />
            </tr>
          </thead>
          <tbody className="divide-y">
            {(webhooks ?? []).map((w) => (
              <tr key={w.id}>
                <td className="px-4 py-3">
                  <span className="font-mono text-xs break-all">{w.url}</span>
                </td>
                <td className="px-4 py-3">
                  <div className="flex flex-wrap gap-1">
                    {w.events.map((e) => (
                      <span key={e} className="rounded-full bg-muted px-2 py-0.5 text-xs">{e}</span>
                    ))}
                  </div>
                </td>
                <td className="px-4 py-3">
                  <button
                    onClick={() => handleToggle(w.id, w.is_active)}
                    className={`rounded-full px-2 py-0.5 text-xs font-medium ${
                      w.is_active
                        ? "bg-green-100 text-green-700 hover:bg-green-200"
                        : "bg-muted text-muted-foreground hover:bg-muted/80"
                    }`}
                  >
                    {w.is_active ? "Active" : "Paused"}
                  </button>
                </td>
                <td className="px-4 py-3 text-muted-foreground text-xs">{formatDate(w.created_at)}</td>
                <td className="px-4 py-3 text-right">
                  <button
                    onClick={() => handleDelete(w.id)}
                    className="rounded p-1 text-muted-foreground hover:text-destructive"
                  >
                    <Trash2 className="h-4 w-4" />
                  </button>
                </td>
              </tr>
            ))}
            {(webhooks ?? []).length === 0 && (
              <tr>
                <td colSpan={5} className="px-4 py-8 text-center text-muted-foreground text-sm">
                  No webhooks configured. Add one above.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}

// ── Platform settings shared helpers ─────────────────────────────────────────

function SettingRow({
  label,
  description,
  children,
}: {
  label: string;
  description?: string;
  children: React.ReactNode;
}) {
  return (
    <div className="flex flex-col gap-1 sm:flex-row sm:items-start sm:justify-between sm:gap-4 py-3 border-b last:border-b-0">
      <div className="flex-1">
        <p className="text-sm font-medium">{label}</p>
        {description && <p className="text-xs text-muted-foreground mt-0.5">{description}</p>}
      </div>
      <div className="sm:flex-shrink-0 sm:w-64">{children}</div>
    </div>
  );
}

function NumberInput({
  value,
  onChange,
  min,
  max,
  step = 0.01,
}: {
  value: number;
  onChange: (v: number) => void;
  min?: number;
  max?: number;
  step?: number;
}) {
  return (
    <input
      type="number"
      value={value}
      min={min}
      max={max}
      step={step}
      onChange={(e) => onChange(parseFloat(e.target.value))}
      className="w-full rounded-md border px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-primary"
    />
  );
}

function Toggle({
  checked,
  onChange,
  label,
}: {
  checked: boolean;
  onChange: (v: boolean) => void;
  label: string;
}) {
  return (
    <label className="flex cursor-pointer items-center gap-2">
      <div
        onClick={() => onChange(!checked)}
        className={`relative h-5 w-9 rounded-full transition-colors ${
          checked ? "bg-primary" : "bg-muted"
        }`}
      >
        <span
          className={`absolute top-0.5 left-0.5 h-4 w-4 rounded-full bg-white shadow transition-transform ${
            checked ? "translate-x-4" : "translate-x-0"
          }`}
        />
      </div>
      <span className="text-sm">{label}</span>
    </label>
  );
}

function usePlatformSettings(tenant: string) {
  const qc = useQueryClient();
  const { data, isLoading } = useQuery<PlatformSettings>({
    queryKey: ["platform-settings", tenant],
    queryFn: () => fetchPlatformSettings(tenant),
  });

  const mutation = useMutation({
    mutationFn: (patch: Parameters<typeof updatePlatformSettings>[1]) =>
      updatePlatformSettings(tenant, patch),
    onSuccess: (updated) => {
      qc.setQueryData(["platform-settings", tenant], updated);
    },
  });

  const resetMutation = useMutation({
    mutationFn: () => resetPlatformSettings(tenant),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["platform-settings", tenant] }),
  });

  return { data, isLoading, mutation, resetMutation };
}

function SaveBar({
  onSave,
  onReset,
  saving,
  resetting,
}: {
  onSave: () => void;
  onReset: () => void;
  saving: boolean;
  resetting: boolean;
}) {
  return (
    <div className="flex justify-between items-center pt-4">
      <button
        onClick={onReset}
        disabled={resetting}
        className="flex items-center gap-1.5 text-xs text-muted-foreground hover:text-foreground disabled:opacity-50"
      >
        <RotateCcw className="h-3.5 w-3.5" />
        {resetting ? "Resetting…" : "Reset to defaults"}
      </button>
      <button
        onClick={onSave}
        disabled={saving}
        className="rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90 disabled:opacity-50"
      >
        {saving ? "Saving…" : "Save changes"}
      </button>
    </div>
  );
}

// ── PII Tab ───────────────────────────────────────────────────────────────────

function PiiTab({ tenant, qc: _qc }: { tenant: string; qc: ReturnType<typeof useQueryClient> }) {
  const { data, isLoading, mutation, resetMutation } = usePlatformSettings(tenant);
  const [local, setLocal] = useState<PlatformSettings["pii"] | null>(null);

  const current = local ?? data?.pii;

  if (isLoading || !data || !current) {
    return <div className="py-8 text-center text-sm text-muted-foreground">Loading…</div>;
  }

  function toggleEntity(entity: string) {
    if (!current) return;
    const next = current.entities.includes(entity)
      ? current.entities.filter((e) => e !== entity)
      : [...current.entities, entity];
    setLocal({ ...current, entities: next });
  }

  function save() {
    if (!local) return;
    mutation.mutate({ pii: local }, { onSuccess: () => setLocal(null) });
  }

  return (
    <div className="space-y-1">
      <div className="rounded-lg border p-4 space-y-1">
        <h3 className="text-sm font-semibold mb-3">PII Sanitization</h3>
        <p className="text-xs text-muted-foreground mb-4">
          Controls how the platform detects and redacts personally identifiable information before
          sending document text to AI models. Extracted values are always restored before saving.
        </p>

        <SettingRow label="Enable PII sanitization" description="Redact PII before any LLM call">
          <Toggle
            checked={current.enabled}
            onChange={(v) => setLocal({ ...current, enabled: v })}
            label={current.enabled ? "Enabled" : "Disabled"}
          />
        </SettingRow>

        <SettingRow
          label="Detection language"
          description="Primary language for Presidio entity detection"
        >
          <select
            value={current.language}
            onChange={(e) => setLocal({ ...current, language: e.target.value })}
            className="w-full rounded-md border px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-primary"
          >
            <option value="en">English (en)</option>
            <option value="es">Spanish (es)</option>
            <option value="de">German (de)</option>
            <option value="fr">French (fr)</option>
            <option value="it">Italian (it)</option>
            <option value="pt">Portuguese (pt)</option>
          </select>
        </SettingRow>

        <SettingRow
          label="Minimum confidence score"
          description="Presidio detections below this threshold are ignored (0.0–1.0)"
        >
          <NumberInput
            value={current.min_score}
            onChange={(v) => setLocal({ ...current, min_score: v })}
            min={0}
            max={1}
            step={0.05}
          />
        </SettingRow>

        <SettingRow
          label="Detected entity types"
          description="Select which PII categories to redact"
        >
          <div className="flex flex-wrap gap-1.5">
            {(data.available_pii_entities ?? []).map((entity) => (
              <button
                key={entity}
                type="button"
                onClick={() => toggleEntity(entity)}
                className={`rounded-full border px-2.5 py-0.5 text-xs font-medium transition-colors ${
                  current.entities.includes(entity)
                    ? "border-primary bg-primary/10 text-primary"
                    : "border-border text-muted-foreground hover:border-primary/40"
                }`}
              >
                {entity}
              </button>
            ))}
          </div>
        </SettingRow>
      </div>

      <SaveBar
        onSave={save}
        onReset={() => { setLocal(null); resetMutation.mutate(); }}
        saving={mutation.isPending}
        resetting={resetMutation.isPending}
      />
    </div>
  );
}

// ── Extraction Tab ────────────────────────────────────────────────────────────

function ExtractionTab({ tenant, qc: _qc }: { tenant: string; qc: ReturnType<typeof useQueryClient> }) {
  const { data, isLoading, mutation, resetMutation } = usePlatformSettings(tenant);
  const [local, setLocal] = useState<PlatformSettings["extraction"] | null>(null);

  const current = local ?? data?.extraction;

  if (isLoading || !data || !current) {
    return <div className="py-8 text-center text-sm text-muted-foreground">Loading…</div>;
  }

  function save() {
    if (!local) return;
    mutation.mutate({ extraction: local }, { onSuccess: () => setLocal(null) });
  }

  return (
    <div className="space-y-1">
      <div className="rounded-lg border p-4 space-y-1">
        <h3 className="text-sm font-semibold mb-3">Extraction & AI Thresholds</h3>
        <p className="text-xs text-muted-foreground mb-4">
          Confidence thresholds control how extracted field results are classified. The color indicators
          in the review workspace reflect these values.
        </p>

        <SettingRow
          label="Valid threshold (green ✓)"
          description="Fields with confidence ≥ this value are auto-accepted"
        >
          <NumberInput
            value={current.confidence_valid}
            onChange={(v) => setLocal({ ...current, confidence_valid: v })}
            min={0}
            max={1}
            step={0.05}
          />
        </SettingRow>

        <SettingRow
          label="Review threshold (yellow ⚠)"
          description="Fields between this and the valid threshold show a warning"
        >
          <NumberInput
            value={current.confidence_review}
            onChange={(v) => setLocal({ ...current, confidence_review: v })}
            min={0}
            max={1}
            step={0.05}
          />
        </SettingRow>

        <SettingRow
          label="Flag threshold (red ✗)"
          description="Fields below this value are flagged for mandatory human review"
        >
          <NumberInput
            value={current.confidence_flag}
            onChange={(v) => setLocal({ ...current, confidence_flag: v })}
            min={0}
            max={1}
            step={0.05}
          />
        </SettingRow>

        <SettingRow
          label="LLM temperature"
          description="Sampling temperature for AI extraction (0 = deterministic)"
        >
          <NumberInput
            value={current.temperature}
            onChange={(v) => setLocal({ ...current, temperature: v })}
            min={0}
            max={1}
            step={0.05}
          />
        </SettingRow>

        <SettingRow
          label="Max output tokens"
          description="Maximum tokens the AI model can generate per extraction call"
        >
          <NumberInput
            value={current.max_tokens}
            onChange={(v) => setLocal({ ...current, max_tokens: Math.round(v) })}
            min={256}
            max={8192}
            step={256}
          />
        </SettingRow>
      </div>

      <div className="rounded-lg border border-muted bg-muted/20 px-4 py-3 text-xs text-muted-foreground">
        <strong>Threshold hierarchy:</strong> flag &lt; review &lt; valid.
        Example defaults: flag = 0.70, review = 0.65, valid = 0.85.
        Ensure flag ≤ review ≤ valid to avoid conflicting classifications.
      </div>

      <SaveBar
        onSave={save}
        onReset={() => { setLocal(null); resetMutation.mutate(); }}
        saving={mutation.isPending}
        resetting={resetMutation.isPending}
      />
    </div>
  );
}

// ── Pipeline Tab ──────────────────────────────────────────────────────────────

function PipelineTab({ tenant, qc: _qc }: { tenant: string; qc: ReturnType<typeof useQueryClient> }) {
  const { data, isLoading, mutation, resetMutation } = usePlatformSettings(tenant);
  const [local, setLocal] = useState<PlatformSettings["pipeline"] | null>(null);

  const current = local ?? data?.pipeline;

  if (isLoading || !data || !current) {
    return <div className="py-8 text-center text-sm text-muted-foreground">Loading…</div>;
  }

  function save() {
    if (!local) return;
    mutation.mutate({ pipeline: local }, { onSuccess: () => setLocal(null) });
  }

  return (
    <div className="space-y-1">
      <div className="rounded-lg border p-4 space-y-1">
        <h3 className="text-sm font-semibold mb-3">Pipeline Limits</h3>
        <p className="text-xs text-muted-foreground mb-4">
          Controls resource limits and timeouts for the document processing pipeline.
          Changes take effect for new uploads; documents already in the queue use the values at enqueue time.
        </p>

        <SettingRow
          label="Max upload size (MB)"
          description="PDF files larger than this are rejected at upload"
        >
          <NumberInput
            value={current.max_file_size_mb}
            onChange={(v) => setLocal({ ...current, max_file_size_mb: Math.round(v) })}
            min={1}
            max={500}
            step={10}
          />
        </SettingRow>

        <SettingRow
          label="Max pages per document"
          description="Documents with more pages than this are rejected"
        >
          <NumberInput
            value={current.max_pages}
            onChange={(v) => setLocal({ ...current, max_pages: Math.round(v) })}
            min={1}
            max={2000}
            step={50}
          />
        </SettingRow>

        <SettingRow
          label="Pipeline timeout (seconds)"
          description="Maximum total processing time before a document is marked failed"
        >
          <NumberInput
            value={current.timeout_seconds}
            onChange={(v) => setLocal({ ...current, timeout_seconds: Math.round(v) })}
            min={30}
            max={600}
            step={30}
          />
        </SettingRow>

        <SettingRow
          label="OCR parallel workers"
          description="Number of parallel OCR processes (higher = faster but more CPU)"
        >
          <NumberInput
            value={current.ocr_workers}
            onChange={(v) => setLocal({ ...current, ocr_workers: Math.round(v) })}
            min={1}
            max={16}
            step={1}
          />
        </SettingRow>
      </div>

      <SaveBar
        onSave={save}
        onReset={() => { setLocal(null); resetMutation.mutate(); }}
        saving={mutation.isPending}
        resetting={resetMutation.isPending}
      />
    </div>
  );
}
