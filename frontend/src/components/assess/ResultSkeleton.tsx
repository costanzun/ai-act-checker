import { Skeleton } from "@/components/ui/skeleton";

export function ResultSkeleton({ withReasoning = true }: { withReasoning?: boolean }) {
  return (
    <div className="space-y-8" aria-hidden data-testid="result-skeleton">
      <Skeleton className="h-44 w-full" />
      {withReasoning && <div className="space-y-2"><Skeleton className="h-6 w-40" /><Skeleton className="h-4 w-full" /><Skeleton className="h-4 w-11/12" /><Skeleton className="h-4 w-2/3" /></div>}
      <div className="space-y-2"><Skeleton className="h-6 w-48" /><Skeleton className="h-20 w-full" /><Skeleton className="h-20 w-full" /></div>
    </div>
  );
}
