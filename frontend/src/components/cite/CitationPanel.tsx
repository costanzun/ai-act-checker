"use client";

import { useEffect, useState } from "react";
import { Sheet, SheetContent, SheetDescription, SheetHeader, SheetTitle } from "@/components/ui/sheet";
import { Skeleton } from "@/components/ui/skeleton";
import { Button } from "@/components/ui/button";
import { useT } from "@/i18n";
import { citeLabel, fetchLawCached } from "@/lib/cite";
import type { Lang, LawResponse } from "@/lib/types";
import { ProvisionBody } from "./ProvisionBody";

type State = { key: string; data: LawResponse | null; error: boolean };

export function CitationPanel({ id, onClose }: { id: string | null; onClose: () => void }) {
  const { lang, t } = useT();
  const [override, setOverride] = useState<{ id: string; lang: Lang } | null>(null);
  const [state, setState] = useState<State | null>(null);
  const panelLang = override && override.id === id ? override.lang : lang;
  const key = id ? `${panelLang}:${id}` : "";

  useEffect(() => {
    if (!id) return;
    let cancelled = false;
    fetchLawCached(id, panelLang)
      .then((data) => !cancelled && setState({ key: `${panelLang}:${id}`, data, error: false }))
      .catch(() => !cancelled && setState({ key: `${panelLang}:${id}`, data: null, error: true }));
    return () => { cancelled = true; };
  }, [id, panelLang]);

  const current = state && state.key === key ? state : null;
  const label = id ? (current?.data?.provision.label ?? citeLabel(id, panelLang)) : "";

  return (
    <Sheet open={id !== null} onOpenChange={(o) => { if (!o) onClose(); }}>
      <SheetContent side="right" className="w-full overflow-y-auto sm:max-w-lg" data-testid="citation-panel">
        <SheetHeader className="border-b border-border pr-12">
          <p className="text-xs uppercase tracking-wider text-muted-foreground">{t("cite.panel.title")}</p>
          <SheetTitle className="font-heading text-2xl">{label}</SheetTitle>
          <SheetDescription className="sr-only">{t("cite.panel.title")}</SheetDescription>
          <div className="mt-2 flex items-center gap-2" role="group" aria-label={t("cite.language")}>
            {(["en", "it"] as const).map((l) => (
              <Button key={l} size="xs" variant={panelLang === l ? "default" : "outline"} aria-pressed={panelLang === l}
                onClick={() => id && setOverride({ id, lang: l })}>{l.toUpperCase()}</Button>
            ))}
          </div>
        </SheetHeader>
        <div className="px-4 pb-8">
          {!current && (
            <div className="space-y-3" aria-busy="true" aria-label={t("cite.loading")}>
              <Skeleton className="h-4 w-1/2" /><Skeleton className="h-5 w-3/4" /><Skeleton className="h-24 w-full" />
            </div>
          )}
          {current?.error && <p role="alert" className="text-sm text-destructive">{t("cite.error")}</p>}
          {current?.data && <ProvisionBody data={current.data} />}
        </div>
      </SheetContent>
    </Sheet>
  );
}
