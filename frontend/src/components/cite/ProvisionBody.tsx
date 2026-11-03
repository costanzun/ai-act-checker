"use client";

import { ExternalLink } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { useT } from "@/i18n";
import type { LawResponse } from "@/lib/types";
import Link from "next/link";

/** Shared body for the CitationPanel and the /law/[id] page. */
export function ProvisionBody({ data, asPage = false }: { data: LawResponse; asPage?: boolean }) {
  const { t } = useT();
  const p = data.provision;
  const paragraphs = (data.full_text || p.text).split(/\n{2,}/).filter(Boolean);
  const amendKey = p.amendment?.kind === "inserted" ? "cite.amended.inserted" : p.amendment?.kind === "deleted" ? "cite.amended.deleted" : "cite.amended";
  return (
    <div className="space-y-4">
      {data.breadcrumb.length > 0 && (
        <nav aria-label="Breadcrumb" className="text-xs text-muted-foreground">
          <ol className="flex flex-wrap items-center gap-x-1.5">
            {data.breadcrumb.map((b, i) => (
              <li key={`${b.id}-${i}`} className="flex items-center gap-1.5">
                {i > 0 && <span aria-hidden>›</span>}
                {b.id.includes(":") ? <Link className="underline-offset-2 hover:underline" href={`/law/${encodeURIComponent(b.id)}`}>{b.label}</Link> : <span>{b.label}</span>}
              </li>
            ))}
          </ol>
        </nav>
      )}
      <div className="flex flex-wrap items-center gap-2">
        {p.amendment && <Badge variant="outline" className="border-eu/40 text-eu">{t(amendKey)}</Badge>}
        {p.type === "guidance" && <Badge variant="secondary">{t("cite.guidance")}</Badge>}
      </div>
      {p.title && p.type !== "recital" && <p className="font-heading text-lg leading-snug">{p.title}</p>}
      <div className="space-y-3 border-l border-border pl-4 text-[0.95rem] leading-relaxed">
        {paragraphs.map((para, i) => <p key={i}>{para}</p>)}
      </div>
      {data.children.length > 0 && (
        <div className="text-sm text-muted-foreground">
          <p className="mb-1 font-medium">{t("cite.children")}</p>
          <ul className="flex flex-wrap gap-2">
            {data.children.map((c) => (
              <li key={c.id}><Link className="font-mono text-xs text-eu underline-offset-2 hover:underline" href={`/law/${encodeURIComponent(c.id)}`}>{c.label}</Link></li>
            ))}
          </ul>
        </div>
      )}
      <div className="flex flex-wrap gap-4 pt-1 text-sm">
        <a className="inline-flex items-center gap-1 text-eu underline-offset-2 hover:underline" href={data.eurlex_url} target="_blank" rel="noopener noreferrer">
          {t("cite.eurlex")} <ExternalLink className="size-3.5" aria-hidden />
        </a>
        {!asPage && (
          <Link className="text-eu underline-offset-2 hover:underline" href={`/law/${encodeURIComponent(p.id)}`}>{t("cite.fullPage")}</Link>
        )}
      </div>
    </div>
  );
}
