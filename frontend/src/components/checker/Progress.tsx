"use client";

import { useEffect, useState } from "react";
import { Check } from "lucide-react";
import { DogScene } from "@/components/pixel/Pixel";
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
  const SEGS = 20;
  const filled = Math.round((pct / 100) * SEGS);

  return (
    <div role="status" aria-live="polite" data-testid="progress"
      className="px-block fade-up mx-2 mb-2 flex flex-col gap-4 overflow-hidden rounded-[1.4rem] px-5 pb-5 pt-5 sm:mx-2.5 sm:mb-2.5 sm:flex-row sm:items-center sm:gap-7 sm:px-7"
      style={{ "--block": "var(--block-loading)", "--grid": "5px" } as React.CSSProperties}>
      <DogScene scene="loading" label={t("scene.loading")} className="w-[200px] shrink-0 max-sm:mx-auto sm:w-[240px]" />
      <div className="min-w-0 flex-1">
        <div className="flex items-center justify-between gap-3">
          <p className="pixel-label">{t("progress.eyebrow")}</p>
          <span className="num text-[13px] font-semibold">{t("progress.elapsed", { s: secs })}</span>
        </div>
        <p className="display mt-2 text-[28px] sm:text-[34px]">{t("progress.title")}</p>
        <div className="mt-4 flex gap-[3px]" aria-hidden>
          {Array.from({ length: SEGS }, (_, i) => (
            <span key={i} className={cn("h-3 flex-1 transition-colors duration-300", i < filled ? "bg-[#111]" : "bg-white/55")} />
          ))}
        </div>
        <ol className="mt-4 flex flex-wrap gap-x-5 gap-y-2">
          {STEPS.map((s, i) => {
            const done = i < cur;
            const active = i === cur || (cur < 0 && i === 0);
            return (
              <li key={s.stage} className="flex items-center gap-2 text-[14px] font-semibold" data-state={done ? "done" : active ? "active" : "pending"}>
                <span className={cn("flex size-5 items-center justify-center rounded-full border-2 border-[#111]",
                  done ? "bg-[#111] text-white" : active ? "bg-white" : "bg-transparent")}>
                  {done ? <Check className="size-3" strokeWidth={3} aria-hidden /> : active ? <span className="size-1.5 bg-[#111]" /> : null}
                </span>
                <span className={cn(active && "shimmer-text", !done && !active && "opacity-70")}>{t(s.key)}</span>
              </li>
            );
          })}
        </ol>
        <button type="button" onClick={onCancel} className="pill pill-secondary mt-5 h-11 border-[#111] bg-white px-5 text-[14px] text-[#111] max-sm:w-full">{t("progress.cancel")}</button>
      </div>
    </div>
  );
}
