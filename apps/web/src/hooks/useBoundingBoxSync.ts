// SPDX-License-Identifier: AGPL-3.0-or-later
"use client";

import { useCallback, useState } from "react";
import type { ExtractedField, BoundingBox } from "@openidp/shared-types";

type PdfViewerRef = { scrollToPage(n: number): void } | null;

export function useBoundingBoxSync(
  pdfRef: React.RefObject<PdfViewerRef>,
  fields: ExtractedField[]
) {
  const [highlightedBbox, setHighlightedBbox] = useState<BoundingBox | null>(null);
  const [highlightedFieldId, setHighlightedFieldId] = useState<string | null>(null);

  const syncFieldToPdf = useCallback(
    (field: ExtractedField) => {
      if (!field.bounding_box) return;
      setHighlightedBbox(field.bounding_box);
      setHighlightedFieldId(field.id);
      if (field.bounding_box.page !== undefined) {
        pdfRef.current?.scrollToPage(field.bounding_box.page);
      }
    },
    [pdfRef]
  );

  const syncPdfToField = useCallback(
    (fieldId: string) => {
      const field = fields.find((f) => f.id === fieldId);
      if (!field) return;
      setHighlightedFieldId(fieldId);
      setHighlightedBbox(field.bounding_box ?? null);
    },
    [fields]
  );

  const clearSync = useCallback(() => {
    setHighlightedBbox(null);
    setHighlightedFieldId(null);
  }, []);

  return { highlightedBbox, highlightedFieldId, syncFieldToPdf, syncPdfToField, clearSync };
}
