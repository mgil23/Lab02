// SPDX-License-Identifier: AGPL-3.0-or-later
import { Sidebar } from "@/components/layout/sidebar";

export default function TenantLayout({
  children,
  params,
}: {
  children: React.ReactNode;
  params: { tenant: string };
}) {
  return (
    <div className="flex h-screen overflow-hidden">
      <Sidebar tenantSlug={params.tenant} />
      <main className="flex-1 overflow-auto">{children}</main>
    </div>
  );
}
