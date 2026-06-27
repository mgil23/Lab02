// SPDX-License-Identifier: AGPL-3.0-or-later
"use client";

import { useQuery } from "@tanstack/react-query";
import { FileText, Clock, CheckCircle, AlertCircle, XCircle } from "lucide-react";
import { fetchKpi, type KpiData } from "@/lib/api";
import { formatDuration } from "@/lib/utils";

function KpiCard({
  label,
  value,
  sub,
  icon: Icon,
  color,
}: {
  label: string;
  value: string | number;
  sub?: string;
  icon: React.ElementType;
  color: string;
}) {
  return (
    <div className="rounded-lg border bg-card p-5 space-y-2">
      <div className="flex items-center justify-between">
        <span className="text-sm font-medium text-muted-foreground">{label}</span>
        <div className={`rounded-full p-2 ${color}`}>
          <Icon className="h-4 w-4" />
        </div>
      </div>
      <p className="text-2xl font-bold tracking-tight">{value}</p>
      {sub && <p className="text-xs text-muted-foreground">{sub}</p>}
    </div>
  );
}

export function KPICards({ tenant }: { tenant: string }) {
  const { data } = useQuery<KpiData>({
    queryKey: ["kpi", tenant],
    queryFn: () => fetchKpi(tenant),
    refetchInterval: 30_000,
  });

  if (!data) return null;

  return (
    <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5">
      <KpiCard
        label="Total Documents"
        value={data.total_documents.toLocaleString()}
        icon={FileText}
        color="bg-blue-50 text-blue-600"
      />
      <KpiCard
        label="Processing"
        value={data.processing}
        sub={`${data.completed} completed`}
        icon={Clock}
        color="bg-yellow-50 text-yellow-600"
      />
      <KpiCard
        label="Pages Processed Today"
        value={data.pages_processed_today.toLocaleString()}
        sub={data.avg_processing_ms ? `Avg ${formatDuration(data.avg_processing_ms)}` : "pages processed"}
        icon={CheckCircle}
        color="bg-green-50 text-green-600"
      />
      <KpiCard
        label="Needs Review"
        value={data.needs_review}
        icon={AlertCircle}
        color="bg-orange-50 text-orange-600"
      />
      <KpiCard
        label="Failed"
        value={data.failed ?? 0}
        icon={XCircle}
        color="bg-red-50 text-red-600"
      />
    </div>
  );
}
