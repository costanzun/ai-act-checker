"use client";

import { Check, Circle } from "lucide-react";
import { useT } from "@/i18n";
import type { Stage } from "@/lib/types";
import { cn } from "@/lib/utils";

const ORDER: Stage[] = ["extracting", "retrieving", "classifying", "drafting"];

/** Shows SSE stage events: done steps get a check, the current step shimmers. */
export function StageTimeline({ seen }: { seen: Stage[] }) {
  const { t } = useT();
  const current = seen[seen.length - 1];
  const curIdx = current ? ORDER.indexOf(current === "finalising" ? "drafting" : current) : -1;
  return (
    <div role="status" aria-live="polite" data-testid="stage-timeline">
      <h2 className="font-heading text-2xl font-medium">{t("assess.running")}</h2>
      <p className="mt-1 text-sm text-muted-foreground">{t("assess.running.hint")}</p>
      <ol className="mt-5 space-y-3">
        {ORDER.map((s, i) => {
          const done = i < curIdx || current === "finalising";
          const active = i === curIdx && current !== "finalising";
          return (
            <li key={s} className="flex items-center gap-3" data-state={done ? "done" : active ? "active" : "pending"}>
              <span className={cn("flex size-6 items-center justify-center rounded-full border",
                done ? "border-eu bg-eu text-primary-foreground" : active ? "border-eu text-eu" : "border-border text-muted-foreground")}>
                {done ? <Check className="size-3.5" aria-hidden /> : <Circle className={cn("size-2 fill-current", active && "animate-pulse")} aria-hidden />}
              </span>
              <span className={cn("text-base", active && "shimmer-text font-medium", done && "text-foreground", !done && !active && "text-muted-foreground")}>
                {t(`stage.${s}` as const)}
              </span>
            </li>
          );
        })}
      </ol>
    </div>
  );
}
