"use client";

import { Check } from "lucide-react";
import { useT } from "@/i18n";
import { cn } from "@/lib/utils";

export type StepId = "describe" | "clarify" | "result";
const STEPS: StepId[] = ["describe", "clarify", "result"];

export function Stepper({ current }: { current: StepId }) {
  const { t } = useT();
  const idx = STEPS.indexOf(current);
  return (
    <nav aria-label={t("stepper.label")} data-testid="stepper" className="no-print">
      <ol className="flex items-center gap-2 sm:gap-4">
        {STEPS.map((s, i) => {
          const done = i < idx || (current === "result" && i === idx);
          const active = i === idx && current !== "result";
          return (
            <li key={s} className="flex flex-1 items-center gap-2 sm:gap-3" aria-current={active || (current === "result" && s === "result") ? "step" : undefined}>
              <span
                className={cn(
                  "flex size-7 shrink-0 items-center justify-center rounded-full border text-xs font-medium",
                  done && "border-eu bg-eu text-primary-foreground",
                  active && "border-eu text-eu",
                  !done && !active && "border-border text-muted-foreground",
                )}
              >
                {done ? <Check className="size-3.5" aria-hidden /> : i + 1}
              </span>
              <span className={cn("text-sm", active || done ? "font-medium text-foreground" : "text-muted-foreground")}>{t(`step.${s}` as const)}</span>
              {i < STEPS.length - 1 && <span aria-hidden className={cn("h-px flex-1", i < idx ? "bg-eu" : "bg-border")} />}
            </li>
          );
        })}
      </ol>
    </nav>
  );
}
