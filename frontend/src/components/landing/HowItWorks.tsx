"use client";

import { useT } from "@/i18n";

export function HowItWorks() {
  const { t } = useT();
  const steps = [1, 2, 3] as const;
  return (
    <section aria-labelledby="how-heading" className="border-t border-border py-12">
      <h2 id="how-heading" className="font-heading text-2xl font-medium">{t("landing.how.title")}</h2>
      <ol className="mt-6 grid gap-6 md:grid-cols-3">
        {steps.map((n) => (
          <li key={n} className="relative border-t-2 border-eu pt-4">
            <span className="font-mono text-xs text-muted-foreground">0{n}</span>
            <h3 className="mt-1 font-heading text-xl font-medium">{t(`landing.how.${n}.title` as const)}</h3>
            <p className="mt-2 text-sm leading-relaxed text-muted-foreground">{t(`landing.how.${n}.text` as const)}</p>
          </li>
        ))}
      </ol>
    </section>
  );
}
