// SPDX-License-Identifier: AGPL-3.0-or-later
"use client";

import { useState } from "react";
import { useParams } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import { CreditCard, ExternalLink, Zap } from "lucide-react";
import { apiClient } from "@/lib/api";

interface BillingInfo {
  plan: string;
  subscription_status: string;
  pages_used_this_month: number;
  pages_limit: number;
}

const PLANS = [
  {
    name: "Starter",
    price: "$49/mo",
    pages: "500 pages",
    users: "1 user",
    features: ["3 document types", "API access", "Webhook notifications"],
  },
  {
    name: "Professional",
    price: "$199/mo",
    pages: "3,000 pages",
    users: "10 users",
    features: ["Unlimited doc types", "Priority processing", "SSO / SAML"],
    highlight: true,
  },
  {
    name: "Enterprise",
    price: "Custom",
    pages: "Unlimited",
    users: "Unlimited",
    features: ["Dedicated support", "SLA guarantee", "On-premise option"],
  },
];

export default function BillingPage() {
  const { tenant } = useParams<{ tenant: string }>();
  const [portalLoading, setPortalLoading] = useState(false);

  const { data: billing } = useQuery<BillingInfo>({
    queryKey: ["billing", tenant],
    queryFn: () => apiClient.get(`/${tenant}/billing/info`),
  });

  async function openPortal() {
    setPortalLoading(true);
    try {
      const res = await apiClient.post<{ url: string }>(`/${tenant}/billing/portal`, {});
      window.location.href = res.url;
    } finally {
      setPortalLoading(false);
    }
  }

  const usagePct = billing
    ? Math.min(100, Math.round((billing.pages_used_this_month / billing.pages_limit) * 100))
    : 0;

  return (
    <div className="p-6 max-w-4xl space-y-8">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Billing</h1>
        <p className="text-muted-foreground text-sm">Manage your subscription and usage.</p>
      </div>

      {billing && (
        <div className="rounded-lg border bg-card p-5 space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="font-semibold capitalize">{billing.plan} Plan</p>
              <p className="text-xs text-muted-foreground capitalize">
                {billing.subscription_status}
              </p>
            </div>
            <button
              onClick={openPortal}
              disabled={portalLoading}
              className="flex items-center gap-1.5 rounded-md border px-3 py-1.5 text-sm hover:bg-muted disabled:opacity-50"
            >
              <ExternalLink className="h-3.5 w-3.5" />
              {portalLoading ? "Opening…" : "Manage Subscription"}
            </button>
          </div>
          <div className="space-y-1">
            <div className="flex justify-between text-xs text-muted-foreground">
              <span>Pages this month</span>
              <span>{billing.pages_used_this_month.toLocaleString()} / {billing.pages_limit.toLocaleString()}</span>
            </div>
            <div className="h-2 overflow-hidden rounded-full bg-muted">
              <div
                className={`h-full rounded-full transition-all ${
                  usagePct > 90 ? "bg-destructive" : usagePct > 70 ? "bg-yellow-500" : "bg-primary"
                }`}
                style={{ width: `${usagePct}%` }}
              />
            </div>
          </div>
        </div>
      )}

      <div>
        <h2 className="text-lg font-semibold mb-4">Plans</h2>
        <div className="grid gap-4 sm:grid-cols-3">
          {PLANS.map((plan) => (
            <div
              key={plan.name}
              className={`rounded-xl border p-5 space-y-4 ${
                plan.highlight ? "border-primary shadow-md" : ""
              }`}
            >
              {plan.highlight && (
                <span className="rounded-full bg-primary/10 px-2 py-0.5 text-[10px] font-semibold text-primary uppercase tracking-wide">
                  Popular
                </span>
              )}
              <div>
                <p className="font-bold text-lg">{plan.name}</p>
                <p className="text-2xl font-bold mt-1">{plan.price}</p>
              </div>
              <div className="text-xs text-muted-foreground space-y-0.5">
                <p className="flex items-center gap-1">
                  <Zap className="h-3 w-3" /> {plan.pages}
                </p>
                <p className="flex items-center gap-1">
                  <CreditCard className="h-3 w-3" /> {plan.users}
                </p>
              </div>
              <ul className="space-y-1">
                {plan.features.map((f) => (
                  <li key={f} className="flex items-center gap-1.5 text-xs">
                    <span className="text-green-500">✓</span> {f}
                  </li>
                ))}
              </ul>
              <button
                onClick={openPortal}
                className={`w-full rounded-md py-2 text-sm font-medium transition-colors ${
                  plan.highlight
                    ? "bg-primary text-primary-foreground hover:bg-primary/90"
                    : "border hover:bg-muted"
                }`}
              >
                {billing?.plan === plan.name.toLowerCase() ? "Current Plan" : "Upgrade"}
              </button>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
