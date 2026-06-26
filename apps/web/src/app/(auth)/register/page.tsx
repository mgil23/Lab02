// SPDX-License-Identifier: AGPL-3.0-or-later
"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { z } from "zod";
import { useAuthStore } from "@/lib/auth";
import { apiClient } from "@/lib/api";

const registerSchema = z.object({
  email: z.string().email(),
  password: z.string().min(8),
  tenant_name: z.string().min(2),
});

export default function RegisterPage() {
  const router = useRouter();
  const setTokens = useAuthStore((s) => s.setTokens);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const data = new FormData(e.currentTarget);
    const parsed = registerSchema.safeParse({
      email: data.get("email"),
      password: data.get("password"),
      tenant_name: data.get("tenant_name"),
    });
    if (!parsed.success) {
      setError("Please fill in all fields correctly.");
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const tokens = await apiClient.post<{
        access_token: string;
        refresh_token: string;
        tenant_slug: string;
      }>("/auth/register", parsed.data);
      setTokens(tokens.access_token, tokens.refresh_token);
      router.push(`/${tokens.tenant_slug}/dashboard`);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Registration failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-muted/30">
      <div className="w-full max-w-md space-y-8 p-8 bg-card rounded-xl border shadow-sm">
        <div className="text-center">
          <h1 className="text-2xl font-bold tracking-tight">OpenIDP SaaS</h1>
          <p className="mt-2 text-sm text-muted-foreground">Create your account</p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          {error && (
            <div className="rounded-md bg-destructive/10 text-destructive px-4 py-3 text-sm">
              {error}
            </div>
          )}
          <div className="space-y-2">
            <label htmlFor="tenant_name" className="text-sm font-medium">
              Organization Name
            </label>
            <input
              id="tenant_name"
              name="tenant_name"
              type="text"
              autoComplete="organization"
              required
              className="w-full rounded-md border px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary"
              placeholder="Acme Corp"
            />
          </div>
          <div className="space-y-2">
            <label htmlFor="email" className="text-sm font-medium">
              Email
            </label>
            <input
              id="email"
              name="email"
              type="email"
              autoComplete="email"
              required
              className="w-full rounded-md border px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary"
              placeholder="you@company.com"
            />
          </div>
          <div className="space-y-2">
            <label htmlFor="password" className="text-sm font-medium">
              Password
            </label>
            <input
              id="password"
              name="password"
              type="password"
              autoComplete="new-password"
              required
              minLength={8}
              className="w-full rounded-md border px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary"
            />
          </div>
          <button
            type="submit"
            disabled={loading}
            className="w-full rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90 disabled:opacity-50"
          >
            {loading ? "Creating account…" : "Create account"}
          </button>
        </form>

        <p className="text-center text-sm text-muted-foreground">
          Already have an account?{" "}
          <Link href="/login" className="text-primary hover:underline">
            Sign in
          </Link>
        </p>
      </div>
    </div>
  );
}
