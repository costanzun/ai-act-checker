"use client";

import { useState } from "react";
import { ArrowRight } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { useT } from "@/i18n";
import { getExamples } from "@/lib/api";
import type { ExampleItem } from "@/lib/types";
import { useEffect } from "react";

export const MIN_CHARS = 20;

export function DescribeForm({ initial, onSubmit }: { initial: string; onSubmit: (text: string) => void }) {
  const { t, lang } = useT();
  const [text, setText] = useState(initial);
  const [examples, setExamples] = useState<ExampleItem[]>([]);
  const n = text.trim().length;
  const valid = n >= MIN_CHARS;

  useEffect(() => {
    let alive = true;
    getExamples(lang).then((r) => alive && setExamples(r.slice(0, 5))).catch(() => undefined);
    return () => { alive = false; };
  }, [lang]);

  return (
    <form
      className="space-y-4"
      onSubmit={(e) => { e.preventDefault(); if (valid) onSubmit(text.trim()); }}
    >
      <Label htmlFor="describe" className="font-heading text-2xl font-medium">{t("assess.describe.label")}</Label>
      <Textarea
        id="describe"
        value={text}
        onChange={(e) => setText(e.target.value)}
        aria-describedby="describe-hint"
        rows={7}
        placeholder={t("landing.card.placeholder")}
        className="min-h-44 bg-card text-base"
      />
      <div id="describe-hint" className="flex flex-wrap justify-between gap-2 text-sm text-muted-foreground">
        <span>{t("assess.describe.hint")}</span>
        <span aria-live="polite" className="font-mono text-xs">
          {t("assess.describe.chars", { n })}{!valid && ` · ${t("assess.describe.more", { n: MIN_CHARS - n })}`}
        </span>
      </div>
      <Button type="submit" size="lg" disabled={!valid} data-testid="describe-submit">
        {t("assess.describe.submit")} <ArrowRight className="size-4" aria-hidden />
      </Button>
      {examples.length > 0 && (
        <div className="space-y-2 border-t border-border pt-4">
          <p className="text-sm text-muted-foreground">{t("assess.describe.examples")}</p>
          <ul className="flex flex-wrap gap-2">
            {examples.map((ex) => (
              <li key={ex.id}>
                <button
                  type="button"
                  onClick={() => setText(ex.text ?? ex.description)}
                  className="rounded-full border border-border px-3 py-1 text-sm transition-colors hover:border-eu hover:text-eu focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                >
                  {ex.title}
                </button>
              </li>
            ))}
          </ul>
        </div>
      )}
    </form>
  );
}
