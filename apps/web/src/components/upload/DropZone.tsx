// SPDX-License-Identifier: AGPL-3.0-or-later
"use client";

import { useRef, useState, type DragEvent } from "react";
import { Upload, FileText } from "lucide-react";
import { cn } from "@/lib/utils";

interface Props {
  onFiles: (files: File[]) => void;
  disabled?: boolean;
}

export function DropZone({ onFiles, disabled }: Props) {
  const [dragging, setDragging] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  function handleDrop(e: DragEvent<HTMLDivElement>) {
    e.preventDefault();
    setDragging(false);
    if (disabled) return;
    const files = Array.from(e.dataTransfer.files).filter(
      (f) => f.type === "application/pdf"
    );
    if (files.length) onFiles(files);
  }

  function handleChange(e: React.ChangeEvent<HTMLInputElement>) {
    const files = Array.from(e.target.files ?? []);
    if (files.length) onFiles(files);
    e.target.value = "";
  }

  return (
    <div
      onDragOver={(e) => { e.preventDefault(); if (!disabled) setDragging(true); }}
      onDragLeave={() => setDragging(false)}
      onDrop={handleDrop}
      onClick={() => !disabled && inputRef.current?.click()}
      className={cn(
        "flex flex-col items-center justify-center rounded-xl border-2 border-dashed p-12 transition-colors cursor-pointer select-none",
        dragging && !disabled
          ? "border-primary bg-primary/5"
          : "border-muted-foreground/30 hover:border-primary/50 hover:bg-muted/30",
        disabled && "opacity-50 cursor-not-allowed"
      )}
    >
      <div className="rounded-full bg-muted p-4 mb-4">
        <Upload className="h-8 w-8 text-muted-foreground" />
      </div>
      <p className="font-medium">Drop PDFs here or click to browse</p>
      <p className="mt-1 text-sm text-muted-foreground">PDF files only · Up to 100 MB each</p>
      <input
        ref={inputRef}
        type="file"
        accept="application/pdf"
        multiple
        onChange={handleChange}
        className="hidden"
      />
    </div>
  );
}
