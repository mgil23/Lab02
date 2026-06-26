// SPDX-License-Identifier: AGPL-3.0-or-later
"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import {
  LayoutDashboard,
  FileText,
  Upload,
  Settings,
  CreditCard,
  Beaker,
  LogOut,
  ChevronLeft,
  ChevronRight,
  Layers,
} from "lucide-react";
import { useState } from "react";
import { cn } from "@/lib/utils";
import { useAuthStore } from "@/lib/auth";

const navItems = (tenant: string) => [
  {
    label: "Dashboard",
    href: `/${tenant}/dashboard`,
    icon: LayoutDashboard,
  },
  {
    label: "Documents",
    href: `/${tenant}/documents`,
    icon: FileText,
  },
  {
    label: "Upload",
    href: `/${tenant}/documents/upload`,
    icon: Upload,
  },
  {
    label: "Doc Types",
    href: `/${tenant}/config/document-types`,
    icon: Layers,
  },
  {
    label: "Playground",
    href: `/${tenant}/playground`,
    icon: Beaker,
  },
  {
    label: "Settings",
    href: `/${tenant}/settings`,
    icon: Settings,
  },
  {
    label: "Billing",
    href: `/${tenant}/billing`,
    icon: CreditCard,
  },
];

export function Sidebar({ tenantSlug }: { tenantSlug: string }) {
  const pathname = usePathname();
  const router = useRouter();
  const clearTokens = useAuthStore((s) => s.clearTokens);
  const [collapsed, setCollapsed] = useState(false);

  function handleLogout() {
    clearTokens();
    router.push("/login");
  }

  return (
    <aside
      className={cn(
        "flex flex-col border-r bg-card transition-all duration-200",
        collapsed ? "w-14" : "w-56"
      )}
    >
      {/* Logo */}
      <div className="flex h-14 items-center border-b px-3">
        {!collapsed && (
          <span className="font-bold text-primary text-sm tracking-tight">OpenIDP</span>
        )}
        <button
          onClick={() => setCollapsed((c) => !c)}
          className="ml-auto rounded p-1 hover:bg-muted"
          aria-label={collapsed ? "Expand sidebar" : "Collapse sidebar"}
        >
          {collapsed ? (
            <ChevronRight className="h-4 w-4" />
          ) : (
            <ChevronLeft className="h-4 w-4" />
          )}
        </button>
      </div>

      {/* Nav */}
      <nav className="flex-1 overflow-y-auto p-2 space-y-0.5">
        {navItems(tenantSlug).map((item) => {
          const active = pathname.startsWith(item.href);
          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                "flex items-center gap-3 rounded-md px-2 py-2 text-sm transition-colors",
                active
                  ? "bg-primary/10 text-primary font-medium"
                  : "text-muted-foreground hover:bg-muted hover:text-foreground"
              )}
            >
              <item.icon className="h-4 w-4 shrink-0" />
              {!collapsed && <span>{item.label}</span>}
            </Link>
          );
        })}
      </nav>

      {/* Footer */}
      <div className="border-t p-2">
        <button
          onClick={handleLogout}
          className="flex w-full items-center gap-3 rounded-md px-2 py-2 text-sm text-muted-foreground hover:bg-muted hover:text-foreground"
        >
          <LogOut className="h-4 w-4 shrink-0" />
          {!collapsed && <span>Sign out</span>}
        </button>
      </div>
    </aside>
  );
}
