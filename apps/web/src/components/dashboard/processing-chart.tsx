// SPDX-License-Identifier: AGPL-3.0-or-later
"use client";

import { useQuery } from "@tanstack/react-query";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from "recharts";
import { fetchProcessingChart, type ChartPoint } from "@/lib/api";

export function ProcessingChart({ tenant }: { tenant: string }) {
  const { data } = useQuery<ChartPoint[]>({
    queryKey: ["processing-chart", tenant],
    queryFn: () => fetchProcessingChart(tenant),
    refetchInterval: 60_000,
  });

  return (
    <div className="rounded-lg border bg-card p-5 space-y-4">
      <div>
        <h3 className="font-semibold">Processing Activity</h3>
        <p className="text-xs text-muted-foreground">Last 7 days</p>
      </div>
      <ResponsiveContainer width="100%" height={220}>
        <BarChart data={data ?? []} margin={{ top: 4, right: 4, left: -16, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" className="stroke-border" />
          <XAxis
            dataKey="date"
            tick={{ fontSize: 11 }}
            tickFormatter={(v: string) =>
              new Date(v).toLocaleDateString("en-US", { weekday: "short" })
            }
          />
          <YAxis tick={{ fontSize: 11 }} allowDecimals={false} />
          <Tooltip
            labelFormatter={(v: string) =>
              new Date(v).toLocaleDateString("en-US", { dateStyle: "medium" })
            }
          />
          <Legend wrapperStyle={{ fontSize: 12 }} />
          <Bar dataKey="completed" name="Completed" fill="hsl(var(--primary))" radius={[3, 3, 0, 0]} />
          <Bar dataKey="failed" name="Failed" fill="hsl(var(--destructive))" radius={[3, 3, 0, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
