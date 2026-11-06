"use client";

import { useT } from "@/i18n";
import { useMeta } from "@/hooks/useMeta";
import Link from "next/link";
import { ArrowLeft } from "lucide-react";
import type { DictKey } from "@/i18n/en";

function Block({ title, keys, vars }: { title: DictKey; keys: DictKey[]; vars?: Record<string, string> }) {
  const { t } = useT();
  return (
    <section className="panel p-5 sm:p-7">
      <h2 className="h-section">{t(title)}</h2>
      <div className="mt-3 max-w-2xl space-y-2.5 text-[15px] leading-relaxed text-ink-2">
        {keys.map((k) => <p key={k}>{t(k, vars)}</p>)}
      </div>
    </section>
  );
}

export function AboutContent() {
  const { t, l, formatDate } = useT();
  const { meta, lawAsOf, checkedAt } = useMeta();
  const celex = meta?.celex ?? "02024R1689-20260727";
  return (
    <article className="mx-auto max-w-3xl py-8 sm:py-12">
      <Link href="/" className="pill pill-secondary h-10 px-4 text-[13.5px]"><ArrowLeft className="size-4" aria-hidden /> {t("law.back")}</Link>
      <h1 className="display mt-4 text-[44px] sm:text-[64px]">{t("about.title")}</h1>
      <p className="mt-3 text-[16px] font-medium">{t("about.lede")}</p>
      <div className="mt-6 space-y-3">
        <Block title="about.method.title" keys={["about.method.1", "about.method.2", "about.method.3", "about.method.4"]} />
        <Block title="about.limits.title" keys={["about.limits.1", "about.limits.2", "about.limits.3", "about.limits.4"]} />
        <Block title="about.sources.title" keys={["about.sources.1", "about.sources.2", "about.sources.3"]} vars={{ celex }} />
        <Block title="about.asOf.title" keys={["about.asOf.text"]} vars={{ asOf: formatDate(lawAsOf), checked: formatDate(checkedAt) }} />
        <section className="panel p-5 sm:p-7">
          <h2 className="h-section">{t("about.model.title")}</h2>
          <p className="num mt-3 text-[13px]" data-testid="about-model">
            {meta ? t("about.model.text", { model: meta.model, provider: meta.provider }) : t("ui.loading")}
          </p>
        </section>
        <section className="panel p-5 sm:p-7">
          <h2 className="h-section">{t("about.disclaimer.title")}</h2>
          <p className="mt-2 text-[13.5px] leading-relaxed text-ink-2">{meta ? l(meta.disclaimer) : t("footer.notLegalAdvice")}</p>
        </section>
      </div>
    </article>
  );
}
