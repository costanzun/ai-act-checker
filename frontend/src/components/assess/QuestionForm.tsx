"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import { useT } from "@/i18n";
import type { Answer, Question } from "@/lib/types";
import { cn } from "@/lib/utils";

type Value = string | number | boolean | null;
const UNKNOWN = "__unknown__";

export const MAX_ROUNDS = 2;

export function QuestionForm({ questions, round, onSubmit }: { questions: Question[]; round: number; onSubmit: (answers: Answer[]) => void }) {
  const { t, l } = useT();
  // undefined = untouched; null = explicit "I don't know"
  const [values, setValues] = useState<Record<string, Value | undefined>>({});
  const set = (id: string, v: Value) => setValues((p) => ({ ...p, [id]: v }));
  const clear = (id: string) => setValues((p) => { const n = { ...p }; delete n[id]; return n; });
  const complete = questions.every((q) => values[q.id] !== undefined);

  const submit = (e: React.FormEvent) => {
    e.preventDefault();
    onSubmit(questions.map((q) => ({ fact_path: q.fact_path, value: values[q.id] ?? null })));
  };

  return (
    <form onSubmit={submit} className="space-y-8" data-testid="question-form">
      <div>
        <p className="font-mono text-xs uppercase tracking-[0.14em] text-eu" data-testid="round-label">{t("clarify.round", { n: round, max: MAX_ROUNDS })}</p>
        <h2 className="mt-2 font-heading text-2xl font-medium sm:text-3xl">{t("clarify.title")}</h2>
        <p className="mt-2 max-w-2xl text-sm text-muted-foreground">{t("clarify.lede")}</p>
      </div>
      <ol className="space-y-8">
        {questions.map((q, i) => {
          const val = values[q.id];
          const opts: { value: string | number | boolean; label: string }[] =
            q.type === "boolean"
              ? [{ value: true, label: t("clarify.yes") }, { value: false, label: t("clarify.no") }, { value: UNKNOWN, label: t("clarify.notSure") }]
              : q.options.map((o) => ({ value: o.value, label: l(o.label) }));
          const groupId = `q-${q.id}`;
          return (
            <li key={q.id} className="border-t border-border pt-5">
              <fieldset className="space-y-3">
                <legend className="font-medium leading-snug">
                  <span className="mr-2 font-mono text-xs text-muted-foreground">{i + 1}.</span>{l(q.text)}
                </legend>
                <p className="text-sm text-muted-foreground">{t("clarify.why", { why: l(q.why) })}</p>
                {q.type === "text" ? (
                  <div className="space-y-2">
                    <Label htmlFor={groupId} className="sr-only">{l(q.text)}</Label>
                    <Input id={groupId} value={typeof val === "string" ? val : ""} placeholder={t("clarify.textPlaceholder")}
                      onChange={(e) => (e.target.value === "" ? clear(q.id) : set(q.id, e.target.value))} />
                  </div>
                ) : (
                  <RadioGroup
                    aria-label={l(q.text)}
                    value={val === undefined ? "" : val === null ? UNKNOWN : String(val)}
                    onValueChange={(sv) => {
                      if (sv === UNKNOWN) return set(q.id, null);
                      const hit = opts.find((o) => String(o.value) === sv);
                      set(q.id, hit ? hit.value : sv);
                    }}
                    className="gap-2"
                  >
                    {opts.map((o) => {
                      const selected = val === undefined ? false : (val === null ? UNKNOWN : String(val)) === String(o.value);
                      return (
                        <Label key={String(o.value)} className={cn("flex cursor-pointer items-center gap-3 rounded-lg border border-border px-3 py-2.5 font-normal transition-colors hover:border-eu/50",
                          selected && "border-eu bg-eu/5")}>
                          <RadioGroupItem value={String(o.value)} />
                          <span>{o.label}</span>
                        </Label>
                      );
                    })}
                  </RadioGroup>
                )}
                {q.type !== "boolean" && <Button type="button" variant="ghost" size="sm" className="text-muted-foreground" onClick={() => set(q.id, null)} aria-pressed={val === null}>
                  {t("clarify.dunno")}
                </Button>}
              </fieldset>
            </li>
          );
        })}
      </ol>
      <div className="flex flex-wrap items-center gap-3 border-t border-border pt-5">
        <Button type="submit" size="lg" disabled={!complete} data-testid="clarify-continue">{t("clarify.continue")}</Button>
        {!complete && <span className="text-sm text-muted-foreground">{t("clarify.answerAll")}</span>}
      </div>
    </form>
  );
}
