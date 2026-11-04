"use client";

import { useState } from "react";
import { Check, ChevronDown, CircleDashed } from "lucide-react";
import { Button } from "@/components/ui/button";
import { CiteList } from "@/components/cite/RichText";
import { useMeta } from "@/hooks/useMeta";
import { useT } from "@/i18n";
import type { Milestone } from "@/lib/types";
import { cn } from "@/lib/utils";

function Row({ m, hot }: { m: Milestone; hot: boolean }) {
  const { t, l, formatDate } = useT();
  const inForce = m.status === "in_force";
  const text = l(m.what);
  return (
    <li
      data-status={m.status}
      data-relevant={hot}
      className={cn("grid grid-cols-[auto_1fr] items-center gap-x-3 gap-y-1 border-l-2 py-2 pr-3 pl-3 md:grid-cols-[9.5rem_minmax(0,1fr)_auto_auto]",
        hot ? "border-l-eu bg-eu/5" : "border-l-transparent")}
    >
      <time dateTime={m.date} className={cn("font-mono text-xs whitespace-nowrap", hot && "font-semibold text-eu")}>{formatDate(m.date)}</time>
      <span title={text} className="min-w-0 truncate text-sm">{text}</span>
      <span className={cn("col-start-1 inline-flex w-fit items-center gap-1 rounded-full px-2 py-0.5 text-[0.7rem] font-medium md:col-start-auto",
        inForce ? "bg-[color:var(--tier-minimal)]/12 text-[color:var(--tier-minimal)]" : "bg-eu/10 text-eu")}>
        {inForce ? <Check className="size-3" aria-hidden /> : <CircleDashed className="size-3" aria-hidden />}
        {t(inForce ? "result.timeline.inForce" : "result.timeline.upcoming")}
      </span>
      <span className="col-span-2 flex flex-wrap items-center gap-x-2 md:col-span-1 md:col-start-auto md:justify-end">
        {hot && <span className="text-[0.7rem] font-medium text-eu">{t("result.timeline.relevant")}</span>}
        <CiteList ids={m.citations} />
      </span>
    </li>
  );
}

/** Compact schedule: milestones relevant to the result first, the rest behind a toggle. */
export function TimelineStrip({ relevant }: { relevant: Milestone[] }) {
  const { t } = useT();
  const { meta } = useMeta();
  const [open, setOpen] = useState(false);
  const all = new Map<string, Milestone>();
  for (const m of [...relevant, ...(meta?.timeline ?? [])]) if (!all.has(m.id)) all.set(m.id, m);
  const hotIds = new Set(relevant.map((m) => m.id));
  const byDate = (a: Milestone, b: Milestone) => a.date.localeCompare(b.date);
  const hot = [...all.values()].filter((m) => hotIds.has(m.id)).sort(byDate);
  const rest = [...all.values()].filter((m) => !hotIds.has(m.id)).sort(byDate);
  if (!all.size) return null;
  return (
    <section aria-labelledby="timeline-heading" data-testid="timeline">
      <h2 id="timeline-heading" className="font-heading text-2xl font-medium">{t("result.timeline")}</h2>
      <div className="mt-4 overflow-hidden rounded-lg border border-border bg-card">
        {hot.length > 0 && <ol className="divide-y divide-border">{hot.map((m) => <Row key={m.id} m={m} hot />)}</ol>}
        {rest.length > 0 && (
          <>
            <ol id="timeline-rest" className={cn("divide-y divide-border border-t border-border print:block", hot.length === 0 && "border-t-0", !open && "hidden")}>
              {rest.map((m) => <Row key={m.id} m={m} hot={false} />)}
            </ol>
            <div className={cn("no-print border-t border-border p-1.5", hot.length === 0 && !open && "border-t-0")}>
              <Button variant="ghost" size="sm" aria-expanded={open} aria-controls="timeline-rest" onClick={() => setOpen((o) => !o)} data-testid="timeline-toggle">
                <ChevronDown className={cn("transition-transform", open && "rotate-180")} aria-hidden />
                {open ? t("result.timeline.hide") : t("result.timeline.showAll", { n: rest.length })}
              </Button>
            </div>
          </>
        )}
      </div>
    </section>
  );
}
