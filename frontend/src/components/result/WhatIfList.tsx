"use client";

import { ArrowRight, RotateCcw } from "lucide-react";
import { RichText } from "@/components/cite/RichText";
import { TierBadge } from "@/components/tier/TierBadge";
import { useT } from "@/i18n";
import type { Assessment, WhatIf } from "@/lib/types";

/** "What would change the answer": engine counterfactuals, each re-checkable in one click, then the assumptions. */
export function WhatIfList({ assessment, onApply }: { assessment: Assessment; onApply: (w: WhatIf) => void }) {
  const { t, l } = useT();
  const items = assessment.what_if ?? [];
  const assumptions = assessment.classification.assumptions;
  if (!items.length && !assumptions.length) return null;

  return (
    <section aria-labelledby="whatif-heading" data-testid="what-if" className="panel p-5 sm:p-7">
      <h2 id="whatif-heading" className="h-section">{t("whatif.title")}</h2>
      {items.length > 0 ? (
        <>
          <p className="mt-1.5 text-[14.5px] text-muted-foreground">{t("whatif.lede")}</p>
          <ul className="mt-3 grid gap-2.5 md:grid-cols-2">
            {items.map((w) => (
              <li key={w.fact_path} data-testid="what-if-item" data-fact={w.fact_path}
                className="flex flex-col gap-3 rounded-2xl bg-surface p-4">
                <p className="text-[15px] font-bold leading-snug tracking-[-0.01em]">{l(w.question)}</p>
                <dl className="grid grid-cols-[auto_1fr] gap-x-2.5 gap-y-1 text-[13.5px]">
                  <dt className="text-muted-foreground">{t("whatif.now")}</dt>
                  <dd className="min-w-0 text-ink-2">{w.unresolved ? <span className="italic">{t("whatif.open")}</span> : l(w.current)}</dd>
                  <dt className="text-muted-foreground">{t("whatif.if")}</dt>
                  <dd className="min-w-0 font-bold">{l(w.answer)}</dd>
                </dl>
                <div className="mt-auto flex flex-wrap items-center justify-between gap-2">
                  <span className="inline-flex flex-wrap items-center gap-1.5 text-[13px] text-muted-foreground">
                    {t("whatif.becomes")} <ArrowRight className="size-3" aria-hidden /> <TierBadge tier={w.tier} />
                  </span>
                  {w.actionable && (
                    <button type="button" onClick={() => onApply(w)} data-testid="what-if-apply"
                      className="pill pill-secondary no-print h-9 px-3.5 text-[13px]">
                      <RotateCcw className="size-3" aria-hidden /> {t("whatif.apply")}
                    </button>
                  )}
                </div>
              </li>
            ))}
          </ul>
        </>
      ) : (
        <p className="mt-1 text-[13px] text-muted-foreground">{t("whatif.none")}</p>
      )}
      {assumptions.length > 0 && (
        <div className="mt-5 border-t-2 border-dashed border-border pt-4" data-testid="uncertainties">
          <h3 className="pixel-label text-muted-foreground">{t("whatif.assumed")}</h3>
          <ul className="mt-2 list-disc space-y-1 pl-5 text-[14px] text-ink-2">
            {assumptions.map((a, i) => <li key={i}><RichText text={l(a)} /></li>)}
          </ul>
        </div>
      )}
    </section>
  );
}
