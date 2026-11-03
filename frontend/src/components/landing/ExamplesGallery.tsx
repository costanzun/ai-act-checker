"use client";

import Link from "next/link";
import type { CSSProperties } from "react";
import { TIER_VAR } from "@/components/tier/tier";
import { useEffect, useState } from "react";
import { ArrowUpRight } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { TierBadge } from "@/components/tier/TierBadge";
import { useT } from "@/i18n";
import { getExamples } from "@/lib/api";
import type { ExampleItem } from "@/lib/types";

export function ExamplesGallery() {
  const { t, lang } = useT();
  const [items, setItems] = useState<ExampleItem[] | null>(null);
  const [failed, setFailed] = useState(false);

  useEffect(() => {
    let alive = true;
    getExamples(lang).then((r) => alive && setItems(r)).catch(() => alive && setFailed(true));
    return () => { alive = false; };
  }, [lang]);

  return (
    <section id="examples" aria-labelledby="examples-heading" className="border-t border-border py-12">
      <h2 id="examples-heading" className="font-heading text-2xl font-medium">{t("landing.examples.title")}</h2>
      <p className="mt-2 max-w-2xl text-sm text-muted-foreground">{t("landing.examples.lede")}</p>
      {failed && <p role="status" className="mt-6 text-sm text-muted-foreground">{t("landing.examples.error")}</p>}
      <ul className="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-3" data-testid="examples-gallery">
        {items === null && !failed
          ? Array.from({ length: 6 }, (_, i) => <li key={i}><Skeleton className="h-40 w-full" /></li>)
          : items?.map((ex) => (
              <li key={ex.id}>
                <Card style={{ "--tc": TIER_VAR[ex.expected_tier] } as CSSProperties} className="relative h-full border border-border shadow-none ring-0 transition-all hover:-translate-y-0.5 hover:border-[var(--tc)] hover:bg-accent/40 focus-within:border-[var(--tc)]">
                  <CardContent className="flex h-full flex-col gap-3">
                    <TierBadge tier={ex.expected_tier} className="self-start" />
                    <h3 className="font-heading text-lg font-medium leading-snug">{ex.title}</h3>
                    <p className="flex-1 text-sm leading-relaxed text-muted-foreground">{ex.description}</p>
                    <Link
                      href={`/assess?example=${encodeURIComponent(ex.id)}&lang=${lang}`}
                      data-testid="example-link"
                      className="inline-flex items-center gap-1 self-start text-sm font-medium text-eu underline-offset-4 after:absolute after:inset-0 hover:underline focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                    >
                      {t("landing.examples.try")} <ArrowUpRight className="size-3.5" aria-hidden />
                      <span className="sr-only"> – {ex.title}</span>
                    </Link>
                  </CardContent>
                </Card>
              </li>
            ))}
      </ul>
    </section>
  );
}
