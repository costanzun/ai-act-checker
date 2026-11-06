"use client";

import { CalendarClock, Gauge, UserRound } from "lucide-react";
import { Cite } from "@/components/cite/Cite";
import { RichText } from "@/components/cite/RichText";
import { OverlayBadge } from "@/components/tier/OverlayBadge";
import { DogScene } from "@/components/pixel/Pixel";
import { TIER_BLOCK, TIER_BLURB_KEY, TIER_KEY, TIER_SCENE } from "@/components/tier/tier";
import { useT } from "@/i18n";
import { CITE_TOKEN } from "@/lib/cite";
import type { Assessment } from "@/lib/types";
import { cn } from "@/lib/utils";
import { firstSentence, keyDeadline, until } from "@/lib/verdict";
import { ExportBar } from "./ExportBar";

function Stat({ icon: Icon, label, value, sub, testId }: { icon: React.ElementType; label: string; value: React.ReactNode; sub?: React.ReactNode; testId?: string }) {
  return (
    <div className="min-w-0" data-testid={testId}>
      <div className="flex items-center gap-1.5 text-[12.5px] font-medium text-muted-foreground">
        <Icon className="size-3.5" strokeWidth={2.2} aria-hidden /> {label}
      </div>
      <div className="mt-1 text-[21px] font-extrabold leading-tight tracking-[-0.03em] sm:text-[24px]">{value}</div>
      {sub && <div className="mt-0.5 text-[13px] text-muted-foreground">{sub}</div>}
    </div>
  );
}

/** The product: a flat colour block with the tier and its dog, then role, key deadline and one sentence of why. */
export function Verdict({ assessment, lawAsOf }: { assessment: Assessment; lawAsOf: string }) {
  const { t, l, formatDate } = useT();
  const c = assessment.classification;
  const dark = c.tier === "out_of_scope";
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
      className="panel fade-up overflow-hidden p-2 sm:p-2.5"
    >
      <div
        className={cn("px-block relative flex flex-col overflow-hidden rounded-[1.4rem] px-5 pt-5 sm:flex-row sm:items-end sm:gap-6 sm:px-8 sm:pt-7", dark && "px-block-dark")}
        style={{ "--block": TIER_BLOCK[c.tier], "--grid": "7px" } as React.CSSProperties}
      >
        <div className="min-w-0 flex-1 sm:pb-8">
          <p className="pixel-label">{t("verdict.label")} · {t(`verdict.eyebrow.${c.tier}` as const)}</p>
          <h2 id="tier-heading" className="display mt-3 text-balance text-[44px] sm:text-[64px] lg:text-[72px]">
            {t(TIER_KEY[c.tier])}
          </h2>
          <p className="mt-3 max-w-md text-[15px] font-medium leading-snug sm:text-[16px]">{t(TIER_BLURB_KEY[c.tier])}</p>
        </div>
        <DogScene
          scene={TIER_SCENE[c.tier]}
          label={t(`scene.${c.tier}` as const)}
          className="mx-auto mt-4 w-[192px] shrink-0 sm:mx-0 sm:mt-0 sm:w-[224px]"
        />
      </div>

      <div className="px-3 pb-3 pt-5 sm:px-6 sm:pb-5 sm:pt-6">
        <p data-testid="verdict-why" className="max-w-3xl text-[17px] leading-relaxed sm:text-[19px]">
          <span className="font-extrabold">{t("verdict.why")}: </span>
          <RichText text={why} />
          {!whyHasCite && decisive?.citations[0] && <> <Cite id={decisive.citations[0]} /></>}
        </p>

        {overlays.length > 0 && (
          <div className="mt-3 flex flex-wrap gap-1.5">{overlays.map((k) => <OverlayBadge key={k} overlay={k} />)}</div>
        )}

        <div className="mt-6 grid grid-cols-1 gap-5 rounded-2xl bg-surface p-4 sm:grid-cols-3 sm:p-5">
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
        {deadline && <p className="mt-3 px-1 text-[13px] text-muted-foreground">{l(deadline.what)}</p>}

        <ExportBar assessment={assessment} className="mt-5" />
        <p className="mt-4 px-1 text-[12px] text-muted-foreground" data-testid="legal-notice">
          {t("verdict.notice", { asOf: formatDate(lawAsOf) })}
        </p>
      </div>
    </section>
  );
}
