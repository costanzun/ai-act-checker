"use client";

import { useEffect, useState } from "react";
import { Check } from "lucide-react";
import { useT } from "@/i18n";
import type { Stage } from "@/lib/types";
import { cn } from "@/lib/utils";

const STEPS: { stage: Stage; key: "stage.extracting" | "stage.classifying" | "stage.retrieving" }[] = [
  { stage: "extracting", key: "stage.extracting" },
  { stage: "classifying", key: "stage.classifying" },
  { stage: "retrieving", key: "stage.retrieving" },
];
const RANK: Record<Stage, number> = { extracting: 0, classifying: 1, retrieving: 2, drafting: 3, finalising: 3 };

/** Live progress while the model reads the description and the rules run. */
export function Progress({ seen, onCancel }: { seen: Stage[]; onCancel: () => void }) {
  const { t } = useT();
  const [secs, setSecs] = useState(0);
  useEffect(() => {
    const t0 = Date.now();
    const id = setInterval(() => setSecs(Math.floor((Date.now() - t0) / 1000)), 250);
    return () => clearInterval(id);
  }, []);
  const cur = seen.length ? RANK[seen[seen.length - 1]] : -1;
  // Reading the description is the long step: creep towards the next milestone while it runs.
  const pct = cur < 0 ? 4 : cur === 0 ? Math.min(55, 8 + secs * 4) : cur === 1 ? 70 : 88;

  return (
    <div role="status" aria-live="polite" data-testid="progress" className="border-t border-hairline bg-card/40 px-4 py-4 sm:px-5">
      <div className="flex items-center justify-between gap-3">
        <p className="text-[13px] font-medium">{t("progress.title")}</p>
        <div className="flex items-center gap-3">
          <span className="num text-[12px] text-muted-foreground">{t("progress.elapsed", { s: secs })}</span>
          <button type="button" onClick={onCancel} className="text-[12px] text-muted-foreground underline-offset-4 hover:text-foreground hover:underline">{t("progress.cancel")}</button>
        </div>
      </div>
      <div className="relative mt-3 h-1.5 overflow-hidden rounded-full bg-raised/70" aria-hidden>
        <div className="absolute inset-y-0 left-0 rounded-full bg-sun transition-[width] duration-500 ease-out" style={{ width: `${pct}%` }} />
        <div className="progress-sweep absolute inset-y-0 w-1/3 bg-gradient-to-r from-transparent via-white/50 to-transparent" />
      </div>
      <ol className="mt-3 flex flex-wrap gap-x-5 gap-y-1.5">
        {STEPS.map((s, i) => {
          const done = i < cur;
          const active = i === cur || (cur < 0 && i === 0);
          return (
            <li key={s.stage} className="flex items-center gap-1.5 text-[12.5px]" data-state={done ? "done" : active ? "active" : "pending"}>
              <span className={cn("flex size-4 items-center justify-center rounded-full border",
                done ? "border-transparent bg-primary text-primary-foreground" : active ? "border-brand" : "border-border")}>
                {done ? <Check className="size-2.5" aria-hidden /> : active ? <span className="size-1.5 animate-pulse rounded-full bg-brand" /> : null}
              </span>
              <span className={cn(active ? "shimmer-text font-medium" : done ? "text-foreground" : "text-muted-foreground")}>{t(s.key)}</span>
            </li>
          );
        })}
      </ol>
    </div>
  );
}
