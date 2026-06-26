// SPDX-License-Identifier: AGPL-3.0-or-later
"use client";

import { useState } from "react";
import { useParams } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import { Beaker, Play, Loader2 } from "lucide-react";
import { fetchDocumentTypes, apiClient } from "@/lib/api";

export default function PlaygroundPage() {
  const { tenant } = useParams<{ tenant: string }>();
  const { data: docTypes } = useQuery({
    queryKey: ["document-types", tenant],
    queryFn: () => fetchDocumentTypes(tenant),
  });

  const [selectedType, setSelectedType] = useState("");
  const [text, setText] = useState("");
  const [result, setResult] = useState<Record<string, unknown> | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function runExtraction() {
    if (!selectedType || !text.trim()) return;
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const res = await apiClient.post<Record<string, unknown>>(
        `/${tenant}/playground/extract`,
        { document_type_slug: selectedType, text }
      );
      setResult(res);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Extraction failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="p-6 max-w-4xl space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight flex items-center gap-2">
          <Beaker className="h-6 w-6 text-primary" />
          Extraction Playground
        </h1>
        <p className="text-muted-foreground text-sm">
          Test field extraction on raw text without uploading a PDF.
        </p>
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <div className="space-y-4">
          <div className="space-y-1.5">
            <label className="text-sm font-medium">Document Type</label>
            <select
              value={selectedType}
              onChange={(e) => setSelectedType(e.target.value)}
              className="w-full rounded-md border px-3 py-2 text-sm bg-background focus:outline-none focus:ring-2 focus:ring-primary"
            >
              <option value="">Select a type…</option>
              {(docTypes ?? []).map((dt) => (
                <option key={dt.id} value={dt.slug}>
                  {dt.name}
                </option>
              ))}
            </select>
          </div>

          <div className="space-y-1.5">
            <label className="text-sm font-medium">Document Text</label>
            <textarea
              value={text}
              onChange={(e) => setText(e.target.value)}
              placeholder="Paste document text here for extraction testing…"
              rows={12}
              className="w-full rounded-md border px-3 py-2 text-sm font-mono focus:outline-none focus:ring-2 focus:ring-primary resize-none"
            />
          </div>

          <button
            onClick={runExtraction}
            disabled={!selectedType || !text.trim() || loading}
            className="flex w-full items-center justify-center gap-2 rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90 disabled:opacity-50"
          >
            {loading ? (
              <>
                <Loader2 className="h-4 w-4 animate-spin" />
                Extracting…
              </>
            ) : (
              <>
                <Play className="h-4 w-4" />
                Run Extraction
              </>
            )}
          </button>
        </div>

        <div className="space-y-2">
          <label className="text-sm font-medium">Result</label>
          {error && (
            <div className="rounded-md bg-destructive/10 p-4 text-sm text-destructive">
              {error}
            </div>
          )}
          {result ? (
            <pre className="overflow-auto rounded-lg border bg-muted p-4 text-xs font-mono h-[calc(100%-2rem)]">
              {JSON.stringify(result, null, 2)}
            </pre>
          ) : (
            <div className="flex h-64 items-center justify-center rounded-lg border border-dashed text-muted-foreground text-sm">
              Results will appear here
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
