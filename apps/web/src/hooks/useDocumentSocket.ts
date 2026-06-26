// SPDX-License-Identifier: AGPL-3.0-or-later
"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import type { PipelineEvent } from "@openidp/shared-types";

type SocketCallbacks = {
  onFieldUpdated?: () => void;
  onStageComplete?: () => void;
  onEvent?: (event: PipelineEvent) => void;
};

const BACKOFF = [1000, 2000, 4000, 8000, 16000];

export function useDocumentSocket(
  tenant: string,
  documentId: string,
  callbacks: SocketCallbacks
) {
  const [status, setStatus] = useState<"connecting" | "connected" | "disconnected">(
    "connecting"
  );
  const [lastEvent, setLastEvent] = useState<PipelineEvent | null>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const retryRef = useRef(0);
  const callbacksRef = useRef(callbacks);
  callbacksRef.current = callbacks;

  const connect = useCallback(() => {
    if (typeof window === "undefined") return;
    const wsBase = process.env.NEXT_PUBLIC_WS_URL ?? "ws://localhost:8000";
    const url = `${wsBase}/api/v1/ws/${tenant}/${documentId}`;
    const ws = new WebSocket(url);
    wsRef.current = ws;

    ws.onopen = () => {
      setStatus("connected");
      retryRef.current = 0;
    };

    ws.onclose = () => {
      setStatus("disconnected");
      const delay = BACKOFF[Math.min(retryRef.current++, BACKOFF.length - 1)]!;
      setTimeout(connect, delay);
    };

    ws.onmessage = (ev) => {
      try {
        const event = JSON.parse(ev.data) as PipelineEvent;
        setLastEvent(event);
        callbacksRef.current.onEvent?.(event);
        if (event.type === "field_updated") callbacksRef.current.onFieldUpdated?.();
        if (event.type === "stage_complete") callbacksRef.current.onStageComplete?.();
      } catch {}
    };
  }, [tenant, documentId]);

  useEffect(() => {
    connect();
    return () => {
      wsRef.current?.close();
    };
  }, [connect]);

  return { status, lastEvent };
}
