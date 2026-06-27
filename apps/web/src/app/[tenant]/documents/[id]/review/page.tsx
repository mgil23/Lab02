// SPDX-License-Identifier: AGPL-3.0-or-later
import { Suspense } from "react";
import { ReviewWorkspace } from "@/components/review-workspace/ReviewWorkspace";

export default function ReviewPage() {
  return (
    <Suspense
      fallback={
        <div className="flex h-screen items-center justify-center">
          <div className="h-8 w-8 animate-spin rounded-full border-2 border-primary border-t-transparent" />
        </div>
      }
    >
      <ReviewWorkspace />
    </Suspense>
  );
}
