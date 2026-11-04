"use client";

import { Cite } from "@/components/cite/Cite";
import { useT } from "@/i18n";
import type { RelatedProvision } from "@/lib/types";

export function RelatedProvisions({ items }: { items: RelatedProvision[] }) {
  const { t, l } = useT();
  return (
    <section aria-labelledby="related-heading">
      <h2 id="related-heading" className="font-heading text-2xl font-medium">{t("result.related")}</h2>
      <p className="mt-1 text-sm text-muted-foreground">{items.length ? t("result.related.lede") : t("result.related.none")}</p>
      <ul className="mt-3 space-y-3">
        {items.map((r) => (
          <li key={r.id} className="grid grid-cols-[auto_1fr] items-start gap-x-3 text-sm">
            <span className="pt-px"><Cite id={r.id} /></span>
            <span className="line-clamp-2 text-muted-foreground">{l(r.why)}</span>
          </li>
        ))}
      </ul>
    </section>
  );
}
