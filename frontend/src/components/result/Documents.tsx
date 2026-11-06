"use client";

import { useEffect, useState } from "react";
import { Checkbox } from "@/components/ui/checkbox";
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

/** Documents to prepare, as a tickable list; ticks persist per assessment in this browser. */
export function Documents({ assessmentId, items }: { assessmentId: string; items: ChecklistItem[] }) {
  const { t, l } = useT();
  const [done, setDone] = useState<string[]>([]);
  const [ready, setReady] = useState(false);

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setDone(load(assessmentId));
    setReady(true);
  }, [assessmentId]);

  if (!items.length) return null;
  const toggle = (id: string, on: boolean) => {
    const next = on ? [...new Set([...done, id])] : done.filter((x) => x !== id);
    setDone(next);
    try { window.localStorage.setItem(key(assessmentId), JSON.stringify(next)); } catch { /* storage unavailable */ }
  };
  const count = items.filter((i) => done.includes(i.id)).length;

  return (
    <section aria-labelledby="checklist-heading" data-testid="checklist" className="panel p-4 sm:p-6">
      <div className="flex flex-wrap items-baseline justify-between gap-2">
        <h2 id="checklist-heading" className="text-[20px] font-normal tracking-tight sm:text-[22px]">{t("docs.title")}</h2>
        <span className="num text-[12.5px] text-muted-foreground" aria-live="polite">{t("docs.progress", { done: count, total: items.length })}</span>
      </div>
      <div className="mt-3 h-1 overflow-hidden rounded-full bg-raised/70" aria-hidden>
        <div className="h-full rounded-full bg-sun transition-[width] duration-300" style={{ width: `${(count / items.length) * 100}%` }} />
      </div>
      <ul className="mt-2 divide-y divide-hairline">
        {items.map((it) => {
          const on = ready && done.includes(it.id);
          return (
            <li key={it.id} className="py-3">
              <label className="flex cursor-pointer items-start gap-3">
                <Checkbox checked={on} onCheckedChange={(v) => toggle(it.id, v === true)} className="mt-0.5 size-[18px] rounded-[5px]" />
                <span className="min-w-0 flex-1">
                  <span className={cn("block text-[14.5px] font-medium leading-snug", on && "text-muted-foreground line-through")}>{l(it.title)}</span>
                  <span className="mt-0.5 block text-[13.5px] leading-relaxed text-muted-foreground">{l(it.description)}</span>
                  {it.template_hint && (
                    <span className="mt-1.5 block rounded-lg border border-dashed border-border bg-card/60 px-2.5 py-1.5 text-[12.5px] text-ink-2">
                      <span className="font-medium">{t("docs.template")}: </span>{l(it.template_hint)}
                    </span>
                  )}
                </span>
              </label>
              {it.citations.length > 0 && <div className="mt-1 pl-[30px]"><CiteList ids={it.citations} /></div>}
            </li>
          );
        })}
      </ul>
      <p className="no-print mt-2 text-[11.5px] text-muted-foreground">{t("docs.saved")}</p>
    </section>
  );
}
