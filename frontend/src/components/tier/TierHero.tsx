"use client";

import { ShieldCheck, ShieldAlert, ShieldQuestion } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { useT } from "@/i18n";
import type { Assessment } from "@/lib/types";
import { RichText } from "@/components/cite/RichText";
import { TIER_BLURB_KEY, TIER_KEY, TIER_VAR } from "./tier";

function firstSentence(s: string): string {
  const m = /^(.+?[.!?])(\s|$)/.exec(s.trim());
  return m ? m[1] : s;
}

export function TierHero({ assessment }: { assessment: Assessment }) {
  const { t, l } = useT();
  const c = assessment.classification;
  const color = TIER_VAR[c.tier];
  const decisive = c.findings.find((f) => f.decisive) ?? c.findings[0];
  const summary = assessment.summary ? l(assessment.summary) : decisive ? firstSentence(l(decisive.rationale)) : t(TIER_BLURB_KEY[c.tier]);
  const Icon = c.confidence === "high" ? ShieldCheck : c.confidence === "medium" ? ShieldQuestion : ShieldAlert;
  return (
    <section
      aria-labelledby="tier-heading"
      data-testid="tier-hero"
      data-tier={c.tier}
      className="relative overflow-hidden rounded-lg border border-border bg-card py-6 pr-5 pl-7 sm:pr-8 sm:pl-9"
    >
      <span aria-hidden className="absolute inset-y-0 left-0 w-1.5" style={{ background: color }} />
      <p className="text-xs font-medium uppercase tracking-[0.14em] text-muted-foreground">{t("tier.label")}</p>
      <h2 id="tier-heading" className="mt-1 font-heading text-4xl font-medium leading-tight sm:text-5xl" style={{ color }}>
        {t(TIER_KEY[c.tier])}
      </h2>
      <p className="mt-3 max-w-2xl text-base leading-relaxed text-foreground/90">
        <span className="sr-only">{t("result.summary.prefix")}: </span>
        <RichText text={summary} />
      </p>
      <p className="mt-2 max-w-2xl text-sm text-muted-foreground">{t(TIER_BLURB_KEY[c.tier])}</p>
      <div className="mt-4 flex flex-wrap items-center gap-2">
        <Badge variant="outline" className="gap-1.5 px-2.5 py-3" data-confidence={c.confidence}>
          <Icon className="size-3.5" aria-hidden />
          {t(`conf.${c.confidence}` as const)}
        </Badge>
        <Badge variant="secondary" className="px-2.5 py-3">{t(`role.${c.role}` as const)}</Badge>
      </div>
    </section>
  );
}
