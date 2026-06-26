// SPDX-License-Identifier: AGPL-3.0-or-later
"use client";

import { useParams } from "next/navigation";
import { DocumentTypeBuilder } from "@/components/document-type-builder/DocumentTypeBuilder";

export default function NewDocumentTypePage() {
  const { tenant } = useParams<{ tenant: string }>();
  return (
    <div className="p-6">
      <DocumentTypeBuilder tenant={tenant} />
    </div>
  );
}
