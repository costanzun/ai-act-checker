"use client";

import { Badge } from "@/components/ui/badge";
import { CiteList, RichText } from "@/components/cite/RichText";
import { useT } from "@/i18n";
import type { Finding } from "@/lib/types";

export function FindingsList({ findings }: { findings: Finding[] }) {
  const { t, l } = useT();
  if (!findings.length) return null;
  return (
    <section aria-labelledby="findings-heading">
      <h2 id="findings-heading" className="font-heading text-2xl font-medium">{t("result.findings")}</h2>
      <ul className="mt-4 divide-y divide-border rounded-lg border border-border bg-card">
        {findings.map((f) => (
          <li key={f.rule_id} className="space-y-2 p-4 sm:p-5">
            <div className="flex flex-wrap items-center gap-2">
              <h3 className="font-medium">{l(f.title)}</h3>
              {f.decisive && <Badge variant="outline" className="border-eu/40 text-eu">{t("result.findings.decisive")}</Badge>}
            </div>
            <p className="text-sm leading-relaxed text-muted-foreground"><RichText text={l(f.rationale)} /></p>
            <CiteList ids={f.citations} />
          </li>
        ))}
      </ul>
    </section>
  );
}
