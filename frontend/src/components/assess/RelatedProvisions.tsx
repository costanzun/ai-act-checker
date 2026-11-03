"use client";

import { Cite } from "@/components/cite/Cite";
import { useT } from "@/i18n";
import type { RelatedProvision } from "@/lib/types";

export function RelatedProvisions({ items }: { items: RelatedProvision[] }) {
  const { t, l } = useT();
  if (!items.length) return null;
  return (
    <section aria-labelledby="related-heading">
      <h2 id="related-heading" className="font-heading text-2xl font-medium">{t("result.related")}</h2>
      <p className="mt-1 text-sm text-muted-foreground">{t("result.related.lede")}</p>
      <ul className="mt-3 space-y-2">
        {items.map((r) => (
          <li key={r.id} className="flex flex-wrap items-baseline gap-2 text-sm"><Cite id={r.id} /><span className="text-muted-foreground">{l(r.why)}</span></li>
        ))}
      </ul>
    </section>
  );
}
