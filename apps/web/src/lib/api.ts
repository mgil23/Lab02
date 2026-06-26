// SPDX-License-Identifier: AGPL-3.0-or-later
import { getStoredAccessToken, useAuthStore } from "./auth";
import type {
  Document,
  DocumentListItem,
  PaginatedResponse,
  SubDocument,
  DocumentType,
} from "@openidp/shared-types";
import type { ExtractedField, ExtractionSummary } from "@openidp/shared-types";

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

class ApiError extends Error {
  constructor(
    public status: number,
    message: string
  ) {
    super(message);
    this.name = "ApiError";
  }
}

async function request<T>(
  path: string,
  options: RequestInit = {}
): Promise<T> {
  const token = getStoredAccessToken();
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(options.headers as Record<string, string>),
  };
  if (token) headers["Authorization"] = `Bearer ${token}`;

  const res = await fetch(`${API_BASE}/api/v1${path}`, { ...options, headers });

  if (res.status === 401) {
    useAuthStore.getState().clearTokens();
    window.location.href = "/login";
    throw new ApiError(401, "Unauthorized");
  }

  if (!res.ok) {
    const body = await res.text();
    let message = body;
    try {
      const parsed = JSON.parse(body);
      message = parsed.detail ?? body;
    } catch {}
    throw new ApiError(res.status, message);
  }

  if (res.status === 204) return undefined as T;
  return res.json();
}

export const apiClient = {
  get: <T>(path: string) => request<T>(path),
  post: <T>(path: string, body: unknown) =>
    request<T>(path, { method: "POST", body: JSON.stringify(body) }),
  patch: <T>(path: string, body: unknown) =>
    request<T>(path, { method: "PATCH", body: JSON.stringify(body) }),
  delete: <T>(path: string) => request<T>(path, { method: "DELETE" }),
};

// ── Document fetchers ──────────────────────────────────────────────────────

export async function fetchDocuments(
  tenant: string,
  params: { status?: string; page?: number; page_size?: number } = {}
): Promise<PaginatedResponse<DocumentListItem>> {
  const qs = new URLSearchParams();
  if (params.status) qs.set("status_filter", params.status);
  if (params.page) qs.set("page", String(params.page));
  if (params.page_size) qs.set("page_size", String(params.page_size));
  return apiClient.get(`/${tenant}/documents?${qs}`);
}

export async function fetchDocument(tenant: string, id: string): Promise<Document> {
  return apiClient.get(`/${tenant}/documents/${id}`);
}

export async function deleteDocument(tenant: string, id: string): Promise<void> {
  return apiClient.delete(`/${tenant}/documents/${id}`);
}

export async function uploadDocument(
  tenant: string,
  file: File,
  onProgress?: (pct: number) => void
): Promise<Document> {
  const token = getStoredAccessToken();
  const form = new FormData();
  form.append("file", file);

  return new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest();
    xhr.open("POST", `${API_BASE}/api/v1/${tenant}/documents`);
    if (token) xhr.setRequestHeader("Authorization", `Bearer ${token}`);
    xhr.upload.onprogress = (e) => {
      if (e.lengthComputable) onProgress?.(Math.round((e.loaded / e.total) * 100));
    };
    xhr.onload = () => {
      if (xhr.status >= 200 && xhr.status < 300) {
        resolve(JSON.parse(xhr.responseText));
      } else {
        reject(new ApiError(xhr.status, xhr.responseText));
      }
    };
    xhr.onerror = () => reject(new Error("Network error"));
    xhr.send(form);
  });
}

// ── SubDocument fetchers ───────────────────────────────────────────────────

export async function fetchSubDocuments(
  tenant: string,
  documentId: string
): Promise<SubDocument[]> {
  return apiClient.get(`/${tenant}/extraction/subdocuments/${documentId}`);
}

// ── Extraction fetchers ────────────────────────────────────────────────────

export async function fetchExtractedFields(
  tenant: string,
  subdocumentId: string
): Promise<ExtractedField[]> {
  const summary: ExtractionSummary = await apiClient.get(
    `/${tenant}/extraction/fields?subdocument_id=${subdocumentId}`
  );
  return summary.fields;
}

export async function patchExtractedField(
  tenant: string,
  fieldId: string,
  body: { human_value: string }
): Promise<ExtractedField> {
  return apiClient.patch(`/${tenant}/extraction/fields/${fieldId}`, body);
}

// ── Dashboard KPI fetchers ─────────────────────────────────────────────────

export interface KpiData {
  total_documents: number;
  processing: number;
  completed: number;
  needs_review: number;
  failed: number;
  pages_processed_today: number;
  avg_processing_ms: number | null;
}

export async function fetchKpi(tenant: string): Promise<KpiData> {
  return apiClient.get(`/${tenant}/documents/kpi`);
}

export interface ChartPoint {
  date: string;
  completed: number;
  failed: number;
}

export async function fetchProcessingChart(tenant: string): Promise<ChartPoint[]> {
  return apiClient.get(`/${tenant}/documents/chart`);
}

// ── Document type fetchers ─────────────────────────────────────────────────

export async function fetchDocumentTypes(tenant: string): Promise<DocumentType[]> {
  return apiClient.get(`/${tenant}/document-types`);
}

export async function fetchDocumentType(
  tenant: string,
  slug: string
): Promise<DocumentType> {
  return apiClient.get(`/${tenant}/document-types/${slug}`);
}
