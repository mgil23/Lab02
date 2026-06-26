// SPDX-License-Identifier: AGPL-3.0-or-later
"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { useParams } from "next/navigation";
import { useSuspenseQuery, useQuery } from "@tanstack/react-query";
import { MessageSquare, Table } from "lucide-react";
import { PDFViewer, type PDFViewerHandle } from "./PDFViewer";
import { KonvaOverlay } from "./KonvaOverlay";
import { ExtractionTable } from "./ExtractionTable";
import { SubDocumentNav } from "./SubDocumentNav";
import { EvidencePanel } from "./EvidencePanel";
import { StatusBanner } from "./StatusBanner";
import { DocumentChat } from "./DocumentChat";
import { useDocumentSocket } from "@/hooks/useDocumentSocket";
import { useBoundingBoxSync } from "@/hooks/useBoundingBoxSync";
import { fetchSubDocuments, fetchExtractedFields } from "@/lib/api";
import { cn } from "@/lib/utils";
import type { ExtractedField } from "@openidp/shared-types";

type RightPanel = "fields" | "chat";

export function ReviewWorkspace() {
  const { tenant, id: documentId } = useParams<{ tenant: string; id: string }>();
  const [activeSubDocId, setActiveSubDocId] = useState<string | null>(null);
  const [selectedFieldId, setSelectedFieldId] = useState<string | null>(null);
  const [currentPage, setCurrentPage] = useState(1);
  const [rightPanel, setRightPanel] = useState<RightPanel>("fields");
  const pdfRef = useRef<PDFViewerHandle | null>(null);

  const { data: subDocs } = useSuspenseQuery({
    queryKey: ["subdocuments", documentId],
    queryFn: () => fetchSubDocuments(tenant, documentId),
  });

  const activeSubDoc = subDocs.find((s) => s.id === activeSubDocId) ?? subDocs[0] ?? null;

  const { data: fields, refetch } = useQuery({
    queryKey: ["fields", activeSubDoc?.id],
    queryFn: () => fetchExtractedFields(tenant, activeSubDoc!.id),
    enabled: !!activeSubDoc,
    initialData: [],
  });

  const { status, lastEvent } = useDocumentSocket(tenant, documentId, {
    onFieldUpdated: refetch,
    onStageComplete: refetch,
  });

  const { highlightedBbox, highlightedFieldId, syncFieldToPdf, syncPdfToField } =
    useBoundingBoxSync(pdfRef, fields ?? []);

  const onFieldSelect = useCallback(
    (field: ExtractedField) => {
      setSelectedFieldId(field.id);
      syncFieldToPdf(field);
    },
    [syncFieldToPdf]
  );

  const onBboxClick = useCallback(
    (fieldId: string) => {
      setSelectedFieldId(fieldId);
      syncPdfToField(fieldId);
    },
    [syncPdfToField]
  );

  useEffect(() => {
    if (!activeSubDocId && subDocs.length > 0) {
      setActiveSubDocId(subDocs[0]!.id);
    }
  }, [subDocs, activeSubDocId]);

  return (
    <div className="flex h-screen flex-col overflow-hidden bg-background">
      <StatusBanner status={status} lastEvent={lastEvent} />
      <SubDocumentNav
        subDocs={subDocs}
        activeId={activeSubDoc?.id ?? null}
        onSelect={setActiveSubDocId}
      />

      <div className="flex flex-1 overflow-hidden">
        {/* PDF Panel */}
        <div className="relative flex-1 min-w-0 border-r">
          <PDFViewer
            ref={pdfRef}
            storageKey={activeSubDoc?.storage_key ?? ""}
            currentPage={currentPage}
            onPageChange={setCurrentPage}
          />
          <KonvaOverlay
            fields={fields ?? []}
            currentPage={currentPage}
            highlightedBbox={highlightedBbox}
            onBboxClick={onBboxClick}
          />
        </div>

        {/* Right Panel */}
        <div className="flex w-[420px] shrink-0 flex-col overflow-hidden">
          {/* Tab bar */}
          <div className="flex border-b shrink-0">
            <button
              onClick={() => setRightPanel("fields")}
              className={cn(
                "flex flex-1 items-center justify-center gap-1.5 py-2 text-xs font-medium transition-colors",
                rightPanel === "fields"
                  ? "border-b-2 border-primary text-primary"
                  : "text-muted-foreground hover:text-foreground"
              )}
            >
              <Table className="h-3.5 w-3.5" />
              Fields
            </button>
            <button
              onClick={() => setRightPanel("chat")}
              className={cn(
                "flex flex-1 items-center justify-center gap-1.5 py-2 text-xs font-medium transition-colors",
                rightPanel === "chat"
                  ? "border-b-2 border-primary text-primary"
                  : "text-muted-foreground hover:text-foreground"
              )}
            >
              <MessageSquare className="h-3.5 w-3.5" />
              Chat
            </button>
          </div>

          {rightPanel === "fields" ? (
            <>
              <ExtractionTable
                fields={fields ?? []}
                selectedFieldId={highlightedFieldId}
                onFieldSelect={onFieldSelect}
                tenant={tenant}
                subDocumentId={activeSubDoc?.id ?? ""}
                onSaved={refetch}
              />
              <EvidencePanel
                field={(fields ?? []).find((f) => f.id === selectedFieldId) ?? null}
              />
            </>
          ) : (
            <DocumentChat tenant={tenant} documentId={documentId} />
          )}
        </div>
      </div>
    </div>
  );
}
