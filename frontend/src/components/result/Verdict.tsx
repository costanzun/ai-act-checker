"use client";

import { CalendarClock, Gauge, UserRound } from "lucide-react";
import { Cite } from "@/components/cite/Cite";
import { RichText } from "@/components/cite/RichText";
import { OverlayBadge } from "@/components/tier/OverlayBadge";
import { TIER_BLURB_KEY, TIER_ICON, TIER_KEY, TIER_VAR } from "@/components/tier/tier";
import { useT } from "@/i18n";
import { CITE_TOKEN } from "@/lib/cite";
import type { Assessment } from "@/lib/types";
import { firstSentence, keyDeadline, until } from "@/lib/verdict";
import { ExportBar } from "./ExportBar";

function Stat({ icon: Icon, label, value, sub, testId }: { icon: React.ElementType; label: string; value: React.ReactNode; sub?: React.ReactNode; testId?: string }) {
  return (
    <div className="min-w-0" data-testid={testId}>
      <div className="flex items-center gap-1.5 text-[12px] text-muted-foreground">
        <Icon className="size-3.5" strokeWidth={1.8} aria-hidden /> {label}
      </div>
      <div className="mt-1 text-[22px] font-light leading-tight tracking-tight sm:text-[26px]">{value}</div>
      {sub && <div className="mt-0.5 text-[12.5px] text-muted-foreground">{sub}</div>}
    </div>
  );
}

/** The product: tier, role and key deadline at a glance, then one sentence of why with its article. */
export function Verdict({ assessment, lawAsOf }: { assessment: Assessment; lawAsOf: string }) {
  const { t, l, formatDate } = useT();
  const c = assessment.classification;
  const color = TIER_VAR[c.tier];
  const Icon = TIER_ICON[c.tier];
  const decisive = c.findings.find((f) => f.decisive) ?? c.findings[0];
  const why = decisive ? firstSentence(l(decisive.rationale)) : t(TIER_BLURB_KEY[c.tier]);
  const whyHasCite = new RegExp(CITE_TOKEN.source).test(why);
  const deadline = keyDeadline(assessment);
  const left = deadline ? until(deadline.date) : null;
  const overlays = (["gpai", "transparency_art50"] as const).filter((k) => (c.overlays[k] ?? []).length > 0);

  const when = !left ? null
    : left.days <= 0 ? t("verdict.already")
    : left.months >= 2 ? t("verdict.inMonths", { n: left.months })
    : left.months === 1 ? t("verdict.inMonth")
    : t("verdict.inDays", { n: left.days });

  return (
    <section
      aria-labelledby="tier-heading"
      data-testid="tier-hero"
      data-tier={c.tier}
      className="panel fade-up relative overflow-hidden p-5 sm:p-7"
      style={{ background: `linear-gradient(140deg, color-mix(in srgb, var(--card) 88%, transparent) 30%, color-mix(in srgb, ${color} 13%, var(--card)) 100%)` }}
    >
      <div className="flex flex-wrap items-center justify-between gap-3">
        <p className="text-[12px] font-medium uppercase tracking-[0.12em] text-muted-foreground">{t("verdict.label")}</p>
        <ExportBar assessment={assessment} className="max-sm:hidden" />
      </div>

      <div className="mt-4 flex items-start gap-3 sm:gap-4">
        <span
          aria-hidden
          className="flex size-12 shrink-0 items-center justify-center rounded-2xl sm:size-14"
          style={{ color, background: `color-mix(in srgb, ${color} 15%, transparent)`, boxShadow: `inset 0 0 0 1px color-mix(in srgb, ${color} 30%, transparent)` }}
        >
          <Icon className="size-6 sm:size-7" strokeWidth={1.8} />
        </span>
        <div className="min-w-0">
          <h2 id="tier-heading" className="text-[32px] font-light leading-[1.05] tracking-tight text-balance sm:text-[46px]" style={{ color }}>
            {t(TIER_KEY[c.tier])}
          </h2>
          <p className="mt-1.5 text-[13.5px] text-muted-foreground">{t(TIER_BLURB_KEY[c.tier])}</p>
        </div>
      </div>

      <p data-testid="verdict-why" className="mt-5 max-w-3xl text-[16px] leading-relaxed sm:text-[17px]">
        <span className="font-medium">{t("verdict.why")}: </span>
        <RichText text={why} />
        {!whyHasCite && decisive?.citations[0] && <> <Cite id={decisive.citations[0]} /></>}
      </p>

      {overlays.length > 0 && (
        <div className="mt-3 flex flex-wrap gap-1.5">{overlays.map((k) => <OverlayBadge key={k} overlay={k} />)}</div>
      )}

      <div className="mt-6 grid grid-cols-1 gap-5 border-t border-dashed border-border pt-5 sm:grid-cols-3">
        <Stat testId="verdict-role" icon={UserRound} label={t("verdict.role")} value={t(`role.short.${c.role}` as const)} sub={t(`role.hint.${c.role}` as const)} />
        <Stat
          testId="verdict-deadline"
          icon={CalendarClock}
          label={t("verdict.deadline")}
          value={deadline ? formatDate(deadline.date) : t("verdict.deadline.none")}
          sub={deadline ? when : null}
        />
        <Stat testId="verdict-confidence" icon={Gauge} label={t("verdict.confidence")} value={t(`conf.short.${c.confidence}` as const)} />
      </div>
      {deadline && <p className="mt-3 text-[12.5px] text-muted-foreground">{l(deadline.what)}</p>}

      <ExportBar assessment={assessment} className="mt-5 sm:hidden" />
      <p className="mt-5 text-[11.5px] text-muted-foreground" data-testid="legal-notice">
        {t("verdict.notice", { asOf: formatDate(lawAsOf) })}
      </p>
    </section>
  );
}
