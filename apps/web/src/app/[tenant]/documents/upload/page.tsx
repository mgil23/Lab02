// SPDX-License-Identifier: AGPL-3.0-or-later
"use client";

import { useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { DropZone } from "@/components/upload/DropZone";
import { UploadProgress, type UploadItem } from "@/components/upload/UploadProgress";
import { uploadDocument } from "@/lib/api";

export default function UploadPage() {
  const { tenant } = useParams<{ tenant: string }>();
  const router = useRouter();
  const [items, setItems] = useState<UploadItem[]>([]);
  const [uploading, setUploading] = useState(false);

  async function handleFiles(files: File[]) {
    setUploading(true);
    const newItems: UploadItem[] = files.map((f) => ({
      id: crypto.randomUUID(),
      filename: f.name,
      progress: 0,
      status: "uploading",
    }));
    setItems((prev) => [...prev, ...newItems]);

    await Promise.allSettled(
      files.map(async (file, idx) => {
        const itemId = newItems[idx]!.id;
        try {
          const doc = await uploadDocument(tenant, file, (pct) => {
            setItems((prev) =>
              prev.map((i) => (i.id === itemId ? { ...i, progress: pct } : i))
            );
          });
          setItems((prev) =>
            prev.map((i) => (i.id === itemId ? { ...i, status: "done", progress: 100 } : i))
          );
          // Navigate to review after last file completes
          if (idx === files.length - 1) {
            setTimeout(() => router.push(`/${tenant}/documents/${doc.id}/review`), 800);
          }
        } catch (e) {
          setItems((prev) =>
            prev.map((i) =>
              i.id === itemId
                ? {
                    ...i,
                    status: "error",
                    error: e instanceof Error ? e.message : "Upload failed",
                  }
                : i
            )
          );
        }
      })
    );

    setUploading(false);
  }

  return (
    <div className="p-6 max-w-2xl mx-auto space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Upload Documents</h1>
        <p className="text-muted-foreground text-sm">
          Upload PDF files for intelligent extraction. Multi-document PDFs are automatically
          split.
        </p>
      </div>

      <DropZone onFiles={handleFiles} disabled={uploading} />

      <UploadProgress items={items} />
    </div>
  );
}
