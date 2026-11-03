"use client";

import { Check, CircleDashed } from "lucide-react";
import { CiteList } from "@/components/cite/RichText";
import { useMeta } from "@/hooks/useMeta";
import { useT } from "@/i18n";
import type { Milestone } from "@/lib/types";
import { cn } from "@/lib/utils";

/** All milestones from /api/meta (falls back to the result's own), highlighting those relevant to this result. */
export function TimelineStrip({ relevant }: { relevant: Milestone[] }) {
  const { t, l, formatDate } = useT();
  const { meta } = useMeta();
  const all = new Map<string, Milestone>();
  for (const m of [...relevant, ...(meta?.timeline ?? [])]) if (!all.has(m.id)) all.set(m.id, m);
  const sorted = [...all.values()].sort((a, b) => a.date.localeCompare(b.date));
  if (!sorted.length) return null;
  const hot = new Set(relevant.map((m) => m.id));
  return (
    <section aria-labelledby="timeline-heading" data-testid="timeline">
      <h2 id="timeline-heading" className="font-heading text-2xl font-medium">{t("result.timeline")}</h2>
      <ol className="mt-4 flex flex-col gap-3 md:flex-row md:gap-0 md:border-t md:border-border">
        {sorted.map((m) => {
          const inForce = m.status === "in_force";
          const isHot = hot.has(m.id);
          return (
            <li key={m.id} data-status={m.status} data-relevant={isHot} aria-current={isHot ? "true" : undefined}
              className={cn("relative flex gap-3 rounded-lg border bg-card p-3 md:min-w-0 md:flex-1 md:flex-col md:rounded-none md:border-0 md:bg-transparent md:p-0 md:pt-4 md:pr-3",
                isHot ? "border-eu ring-1 ring-eu md:ring-0" : "border-border")}>
              <span aria-hidden className={cn("hidden md:absolute md:-top-[5px] md:left-0 md:block md:size-2.5 md:rounded-full",
                inForce ? "bg-[color:var(--tier-minimal)]" : "bg-eu", isHot && "md:size-3 md:-top-[6px] md:ring-4 md:ring-eu/20")} />
              <span className={cn("mt-0.5 shrink-0 md:hidden", inForce ? "text-[color:var(--tier-minimal)]" : "text-eu")} aria-hidden>
                {inForce ? <Check className="size-4" /> : <CircleDashed className="size-4" />}
              </span>
              <div className="min-w-0 space-y-1">
                <div className="flex flex-wrap items-center gap-x-2">
                  <time dateTime={m.date} className={cn("font-mono text-xs", isHot && "font-semibold text-eu")}>{formatDate(m.date)}</time>
                  <span className={cn("inline-flex items-center gap-1 text-[0.7rem] font-medium", inForce ? "text-[color:var(--tier-minimal)]" : "text-eu")}>
                    {inForce && <Check className="hidden size-3 md:inline" aria-hidden />}{t(inForce ? "result.timeline.inForce" : "result.timeline.upcoming")}
                  </span>
                </div>
                <p className="text-xs leading-relaxed text-muted-foreground">{l(m.what)}</p>
                {isHot && <p className="text-[0.7rem] font-medium text-eu">{t("result.timeline.relevant")}</p>}
                <CiteList ids={m.citations} />
              </div>
            </li>
          );
        })}
      </ol>
    </section>
  );
}
