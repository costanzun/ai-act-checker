"use client";

import { HelpCircle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { RichText } from "@/components/cite/RichText";
import { useT } from "@/i18n";
import type { Assessment } from "@/lib/types";

const CORRECTABLE = /^(nothing in the description suggests|nulla nella descrizione suggerisce)/i;

/** Assumptions (classification.assumptions) and open points (uncertainties); hidden when both are empty. */
export function UncertaintiesCallout({ assessment, canAskAgain, onAskAgain }: { assessment: Assessment; canAskAgain: boolean; onAskAgain: () => void }) {
  const { t, l } = useT();
  const assumptions = assessment.classification.assumptions;
  const open = assessment.uncertainties;
  if (!assumptions.length && !open.length) return null;
  return (
    <section aria-labelledby="unc-heading" data-testid="uncertainties" className="rounded-lg border border-border border-l-4 border-l-[color:var(--tier-high)] bg-card p-5">
      <h2 id="unc-heading" className="flex items-center gap-2 font-heading text-2xl font-medium">
        <HelpCircle className="size-5 text-[color:var(--tier-high)]" aria-hidden /> {t("result.uncertainties")}
      </h2>
      <div className="mt-3 grid gap-5 md:grid-cols-2">
        {assumptions.length > 0 && (
          <div>
            <h3 className="text-xs font-medium uppercase tracking-[0.12em] text-muted-foreground">{t("result.uncertainties.assumptions")}</h3>
            <ul className="mt-1 list-disc space-y-1 pl-5 text-sm">
              {assumptions.map((a, i) => (
                <li key={i}>
                  <RichText text={l(a)} />
                  {CORRECTABLE.test(a.en ?? "") || CORRECTABLE.test(a.it ?? "") ? (
                    <button type="button" onClick={onAskAgain} className="no-print ml-2 text-eu underline underline-offset-2 hover:no-underline focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring">{t("unc.correct")}</button>
                  ) : null}
                </li>
              ))}
            </ul>
          </div>
        )}
        {open.length > 0 && (
          <div>
            <h3 className="text-xs font-medium uppercase tracking-[0.12em] text-muted-foreground">{t("result.uncertainties.open")}</h3>
            <ul className="mt-1 list-disc space-y-1 pl-5 text-sm">{open.map((u, i) => <li key={i}><RichText text={l(u)} /></li>)}</ul>
          </div>
        )}
      </div>
      {canAskAgain && <Button variant="outline" className="mt-4 no-print" onClick={onAskAgain}>{t("result.askAgain")}</Button>}
    </section>
  );
}
