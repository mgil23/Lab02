// SPDX-License-Identifier: AGPL-3.0-or-later
"use client";

import { useEffect, useRef } from "react";
import type { ExtractedField, BoundingBox } from "@openidp/shared-types";

interface Props {
  fields: ExtractedField[];
  currentPage: number;
  highlightedBbox: BoundingBox | null;
  onBboxClick: (fieldId: string) => void;
}

export function KonvaOverlay({ fields, currentPage, highlightedBbox, onBboxClick }: Props) {
  const containerRef = useRef<HTMLDivElement>(null);
  const stageRef = useRef<unknown>(null);

  const pageFields = fields.filter(
    (f) => f.bounding_box && f.bounding_box.page === currentPage
  );

  useEffect(() => {
    async function initKonva() {
      if (!containerRef.current) return;
      const Konva = (await import("konva")).default;
      const parent = containerRef.current.parentElement;
      if (!parent) return;

      const width = parent.clientWidth;
      const height = parent.clientHeight;

      if (stageRef.current) {
        (stageRef.current as { destroy(): void }).destroy();
      }

      const stage = new Konva.Stage({
        container: containerRef.current,
        width,
        height,
      });
      stageRef.current = stage;

      const layer = new Konva.Layer();
      stage.add(layer);

      for (const field of pageFields) {
        const bbox = field.bounding_box!;
        const isHighlighted = highlightedBbox
          ? highlightedBbox.x === bbox.x && highlightedBbox.y === bbox.y
          : false;

        const rect = new Konva.Rect({
          x: bbox.x,
          y: bbox.y,
          width: bbox.width,
          height: bbox.height,
          stroke: isHighlighted ? "#2563eb" : "#3b82f6",
          strokeWidth: isHighlighted ? 2.5 : 1.5,
          fill: isHighlighted ? "rgba(37,99,235,0.12)" : "rgba(59,130,246,0.06)",
          cornerRadius: 2,
        });

        rect.on("click", () => onBboxClick(field.id));
        rect.on("mouseenter", () => {
          stage.container().style.cursor = "pointer";
        });
        rect.on("mouseleave", () => {
          stage.container().style.cursor = "default";
        });

        layer.add(rect);
      }

      layer.draw();
    }

    initKonva();

    return () => {
      if (stageRef.current) {
        (stageRef.current as { destroy(): void }).destroy();
        stageRef.current = null;
      }
    };
  }, [pageFields, highlightedBbox, onBboxClick]);

  return (
    <div
      ref={containerRef}
      className="absolute inset-0 pointer-events-none"
      style={{ pointerEvents: pageFields.length > 0 ? "auto" : "none" }}
    />
  );
}
