// SPDX-License-Identifier: AGPL-3.0-or-later
"use client";

import { forwardRef, useEffect, useImperativeHandle, useRef, useState } from "react";
import { ChevronLeft, ChevronRight, ZoomIn, ZoomOut } from "lucide-react";

export interface PDFViewerHandle {
  scrollToPage(n: number): void;
}

interface Props {
  storageKey: string;
  currentPage: number;
  onPageChange: (page: number) => void;
}

export const PDFViewer = forwardRef<PDFViewerHandle, Props>(function PDFViewer(
  { storageKey, currentPage, onPageChange },
  ref
) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const pdfRef = useRef<unknown>(null);
  const renderTaskRef = useRef<{ cancel(): void } | null>(null);
  const [totalPages, setTotalPages] = useState(0);
  const [scale, setScale] = useState(1.2);
  const [loading, setLoading] = useState(false);

  useImperativeHandle(ref, () => ({
    scrollToPage(n: number) {
      onPageChange(n);
    },
  }));

  useEffect(() => {
    if (!storageKey) return;
    let cancelled = false;

    async function loadPdf() {
      setLoading(true);
      try {
        const pdfjs = await import("pdfjs-dist");
        pdfjs.GlobalWorkerOptions.workerSrc = "/pdf.worker.min.mjs";
        const apiBase = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
        const url = `${apiBase}/api/v1/storage/${encodeURIComponent(storageKey)}`;
        const pdf = await pdfjs.getDocument(url).promise;
        if (cancelled) return;
        pdfRef.current = pdf;
        setTotalPages(pdf.numPages);
      } catch (e) {
        console.error("PDF load error", e);
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    loadPdf();
    return () => { cancelled = true; };
  }, [storageKey]);

  useEffect(() => {
    if (!pdfRef.current || !canvasRef.current) return;
    let cancelled = false;

    async function renderPage() {
      if (renderTaskRef.current) {
        renderTaskRef.current.cancel();
        renderTaskRef.current = null;
      }
      const pdf = pdfRef.current as { getPage(n: number): Promise<unknown> };
      const page = await pdf.getPage(currentPage) as {
        getViewport(opts: { scale: number }): { width: number; height: number };
        render(ctx: unknown): { cancel(): void; promise: Promise<void> };
      };
      if (cancelled) return;
      const viewport = page.getViewport({ scale });
      const canvas = canvasRef.current!;
      const ctx = canvas.getContext("2d")!;
      canvas.width = viewport.width;
      canvas.height = viewport.height;
      const task = page.render({ canvasContext: ctx, viewport });
      renderTaskRef.current = task;
      try {
        await task.promise;
      } catch (e) {
        // Cancelled
      }
    }

    renderPage();
    return () => { cancelled = true; };
  }, [pdfRef.current, currentPage, scale]);

  return (
    <div ref={containerRef} className="flex h-full flex-col bg-muted/30">
      {/* Toolbar */}
      <div className="flex items-center gap-2 border-b bg-card px-3 py-1.5 text-xs shrink-0">
        <button
          onClick={() => onPageChange(Math.max(1, currentPage - 1))}
          disabled={currentPage <= 1}
          className="rounded p-1 hover:bg-muted disabled:opacity-30"
        >
          <ChevronLeft className="h-3.5 w-3.5" />
        </button>
        <span className="text-muted-foreground">
          {currentPage} / {totalPages || "…"}
        </span>
        <button
          onClick={() => onPageChange(Math.min(totalPages, currentPage + 1))}
          disabled={currentPage >= totalPages}
          className="rounded p-1 hover:bg-muted disabled:opacity-30"
        >
          <ChevronRight className="h-3.5 w-3.5" />
        </button>
        <div className="ml-auto flex items-center gap-1">
          <button
            onClick={() => setScale((s) => Math.max(0.5, s - 0.2))}
            className="rounded p-1 hover:bg-muted"
          >
            <ZoomOut className="h-3.5 w-3.5" />
          </button>
          <span className="w-10 text-center">{Math.round(scale * 100)}%</span>
          <button
            onClick={() => setScale((s) => Math.min(3, s + 0.2))}
            className="rounded p-1 hover:bg-muted"
          >
            <ZoomIn className="h-3.5 w-3.5" />
          </button>
        </div>
      </div>

      {/* Canvas */}
      <div className="flex-1 overflow-auto flex justify-center p-4">
        {loading ? (
          <div className="flex h-64 w-full items-center justify-center">
            <div className="h-8 w-8 animate-spin rounded-full border-2 border-primary border-t-transparent" />
          </div>
        ) : (
          <canvas ref={canvasRef} className="shadow-md rounded" />
        )}
      </div>
    </div>
  );
});
