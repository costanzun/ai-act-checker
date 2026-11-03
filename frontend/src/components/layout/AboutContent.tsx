"use client";

import { useT } from "@/i18n";
import { useMeta } from "@/hooks/useMeta";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Info } from "lucide-react";
import type { DictKey } from "@/i18n/en";

function Block({ title, keys, vars }: { title: DictKey; keys: DictKey[]; vars?: Record<string, string> }) {
  const { t } = useT();
  return (
    <section className="rule py-8">
      <h2 className="font-heading text-2xl font-medium">{t(title)}</h2>
      <div className="mt-4 max-w-2xl space-y-3 leading-relaxed text-foreground/90">
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
    <article className="mx-auto max-w-3xl py-10 sm:py-14">
      <h1 className="font-heading text-4xl font-medium sm:text-5xl">{t("about.title")}</h1>
      <p className="mt-4 text-lg text-muted-foreground">{t("about.lede")}</p>
      <div className="mt-8">
        <Block title="about.method.title" keys={["about.method.1", "about.method.2", "about.method.3", "about.method.4"]} />
        <Block title="about.limits.title" keys={["about.limits.1", "about.limits.2", "about.limits.3", "about.limits.4"]} />
        <Block title="about.sources.title" keys={["about.sources.1", "about.sources.2", "about.sources.3"]} vars={{ celex }} />
        <Block title="about.asOf.title" keys={["about.asOf.text"]} vars={{ asOf: formatDate(lawAsOf), checked: formatDate(checkedAt) }} />
        <section className="rule py-8">
          <h2 className="font-heading text-2xl font-medium">{t("about.model.title")}</h2>
          <p className="mt-4 font-mono text-sm" data-testid="about-model">
            {meta ? t("about.model.text", { model: meta.model, provider: meta.provider }) : t("ui.loading")}
          </p>
        </section>
        <Alert>
          <Info aria-hidden />
          <AlertTitle>{t("about.disclaimer.title")}</AlertTitle>
          <AlertDescription>{meta ? l(meta.disclaimer) : t("footer.notLegalAdvice")}</AlertDescription>
        </Alert>
      </div>
    </article>
  );
}
