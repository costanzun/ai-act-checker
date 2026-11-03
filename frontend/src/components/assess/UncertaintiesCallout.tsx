"use client";

import { HelpCircle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { RichText } from "@/components/cite/RichText";
import { useT } from "@/i18n";
import type { Assessment } from "@/lib/types";

export function UncertaintiesCallout({ assessment, canAskAgain, onAskAgain }: { assessment: Assessment; canAskAgain: boolean; onAskAgain: () => void }) {
  const { t, l } = useT();
  const c = assessment.classification;
  const hasAny = assessment.uncertainties.length || c.assumptions.length || c.unresolved.length;
  if (!hasAny) return null;
  return (
    <section aria-labelledby="unc-heading" className="rounded-lg border border-border border-l-4 border-l-[color:var(--tier-high)] bg-card p-5">
      <h2 id="unc-heading" className="flex items-center gap-2 font-heading text-2xl font-medium">
        <HelpCircle className="size-5 text-[color:var(--tier-high)]" aria-hidden /> {t("result.uncertainties")}
      </h2>
      {assessment.uncertainties.length > 0 && (
        <ul className="mt-3 list-disc space-y-1 pl-5 text-sm">{assessment.uncertainties.map((u, i) => <li key={i}><RichText text={l(u)} /></li>)}</ul>
      )}
      {c.assumptions.length > 0 && (
        <div className="mt-4">
          <h3 className="text-xs font-medium uppercase tracking-[0.12em] text-muted-foreground">{t("result.uncertainties.assumptions")}</h3>
          <ul className="mt-1 list-disc space-y-1 pl-5 text-sm">{c.assumptions.map((a, i) => <li key={i}>{l(a)}</li>)}</ul>
        </div>
      )}
      {c.unresolved.length > 0 && (
        <div className="mt-4">
          <h3 className="text-xs font-medium uppercase tracking-[0.12em] text-muted-foreground">{t("result.uncertainties.unresolved")}</h3>
          <ul className="mt-1 flex flex-wrap gap-2">{c.unresolved.map((u) => <li key={u} className="rounded border border-border px-2 py-0.5 font-mono text-xs">{u}</li>)}</ul>
        </div>
      )}
      {canAskAgain && (
        <Button variant="outline" className="mt-4 no-print" onClick={onAskAgain}>{t("result.askAgain")}</Button>
      )}
    </section>
  );
}
