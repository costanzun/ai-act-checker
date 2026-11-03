"use client";

import { useEffect, useState } from "react";
import { Checkbox } from "@/components/ui/checkbox";
import { Progress } from "@/components/ui/progress";
import { CiteList } from "@/components/cite/RichText";
import { useT } from "@/i18n";
import type { ChecklistItem } from "@/lib/types";
import { cn } from "@/lib/utils";

const key = (id: string) => `aiact.checklist.${id}`;

function load(id: string): string[] {
  try {
    const raw = window.localStorage.getItem(key(id));
    const parsed: unknown = raw ? JSON.parse(raw) : [];
    return Array.isArray(parsed) ? parsed.filter((x): x is string => typeof x === "string") : [];
  } catch {
    return [];
  }
}

export function Checklist({ assessmentId, items }: { assessmentId: string; items: ChecklistItem[] }) {
  const { t, l } = useT();
  const [done, setDone] = useState<string[]>([]);
  const [ready, setReady] = useState(false);

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setDone(load(assessmentId));
    setReady(true);
  }, [assessmentId]);

  const toggle = (id: string, on: boolean) => {
    const next = on ? [...new Set([...done, id])] : done.filter((x) => x !== id);
    setDone(next);
    try { window.localStorage.setItem(key(assessmentId), JSON.stringify(next)); } catch { /* ignore */ }
  };

  const count = items.filter((i) => done.includes(i.id)).length;
  const pct = items.length ? Math.round((count / items.length) * 100) : 0;
  if (!items.length) return null;

  return (
    <section aria-labelledby="checklist-heading" data-testid="checklist">
      <div className="flex flex-wrap items-end justify-between gap-2">
        <h2 id="checklist-heading" className="font-heading text-2xl font-medium">{t("result.checklist")}</h2>
        <p className="font-mono text-xs text-muted-foreground" aria-live="polite">{t("result.checklist.progress", { done: count, total: items.length })}</p>
      </div>
      <Progress value={pct} aria-label={t("result.checklist")} className="mt-3" />
      <ul className="mt-4 divide-y divide-border rounded-lg border border-border bg-card">
        {items.map((it) => {
          const on = ready && done.includes(it.id);
          return (
            <li key={it.id} className="p-4 sm:p-5">
              <label className="flex cursor-pointer items-start gap-3">
                <Checkbox checked={on} onCheckedChange={(v) => toggle(it.id, v === true)} className="mt-1" />
                <span className="min-w-0 flex-1 space-y-1.5">
                  <span className={cn("block font-medium", on && "text-muted-foreground line-through")}>{l(it.title)}</span>
                  <span className="block text-sm leading-relaxed text-muted-foreground">{l(it.description)}</span>
                  {it.template_hint && (
                    <span className="block rounded-md border border-dashed border-border bg-background px-3 py-2 text-sm">
                      <span className="font-medium">{t("result.checklist.template")}: </span>{l(it.template_hint)}
                    </span>
                  )}
                </span>
              </label>
              {it.citations.length > 0 && <div className="mt-2 pl-7"><CiteList ids={it.citations} /></div>}
            </li>
          );
        })}
      </ul>
      <p className="mt-2 text-xs text-muted-foreground no-print">{t("result.checklist.saved")}</p>
    </section>
  );
}
