// SPDX-License-Identifier: AGPL-3.0-or-later
"use client";

import { Suspense } from "react";
import { KPICards } from "@/components/dashboard/kpi-cards";
import { ProcessingChart } from "@/components/dashboard/processing-chart";
import { RecentDocuments } from "@/components/dashboard/recent-documents";

export default function DashboardPage({ params }: { params: { tenant: string } }) {
  return (
    <div className="p-6 space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Dashboard</h1>
        <p className="text-muted-foreground">Overview of your document processing activity</p>
      </div>

      <Suspense fallback={<div className="h-32 animate-pulse rounded-lg bg-muted" />}>
        <KPICards tenant={params.tenant} />
      </Suspense>

      <div className="grid gap-6 lg:grid-cols-2">
        <Suspense fallback={<div className="h-64 animate-pulse rounded-lg bg-muted" />}>
          <ProcessingChart tenant={params.tenant} />
        </Suspense>
        <Suspense fallback={<div className="h-64 animate-pulse rounded-lg bg-muted" />}>
          <RecentDocuments tenant={params.tenant} />
        </Suspense>
      </div>
    </div>
  );
}
