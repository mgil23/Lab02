// SPDX-License-Identifier: AGPL-3.0-or-later

export type TenantPlan = "free" | "starter" | "professional" | "enterprise";
export type SubscriptionStatus =
  | "trialing"
  | "active"
  | "past_due"
  | "canceled"
  | "paused";

export interface Tenant {
  id: string;
  slug: string;
  name: string;
  plan: TenantPlan;
  subscription_status: SubscriptionStatus;
  settings: Record<string, unknown>;
  created_at: string;
}

export interface User {
  id: string;
  tenant_id: string;
  email: string;
  role: "admin" | "reviewer" | "viewer";
  is_active: boolean;
  created_at: string;
}

export interface ApiKey {
  id: string;
  tenant_id: string;
  name: string;
  scopes: string[];
  last_used_at: string | null;
  expires_at: string | null;
  created_at: string;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
}
