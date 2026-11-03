import { Suspense } from "react";
import { AssessFlow } from "@/components/assess/AssessFlow";
import { Skeleton } from "@/components/ui/skeleton";

export default function AssessPage() {
  return (
    <Suspense fallback={<div className="mx-auto max-w-3xl space-y-4 py-12"><Skeleton className="h-8 w-full" /><Skeleton className="h-48 w-full" /></div>}>
      <AssessFlow />
    </Suspense>
  );
}
