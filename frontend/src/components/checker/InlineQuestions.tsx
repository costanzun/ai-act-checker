"use client";

import { useState } from "react";
import { ArrowRight, HelpCircle } from "lucide-react";
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip";
import { useT } from "@/i18n";
import type { Answer, Question } from "@/lib/types";
import { cn } from "@/lib/utils";

type Value = string | number | boolean | null;
/** Above this many options a compact select replaces the chips. */
const MAX_CHIPS = 5;

function Chip({ on, children, onClick }: { on: boolean; children: React.ReactNode; onClick: () => void }) {
  return (
    <button
      type="button"
      role="radio"
      aria-checked={on}
      onClick={onClick}
      className={cn(
        "min-h-9 rounded-full border px-3.5 py-1.5 text-left text-[13px] leading-snug transition-colors",
        on ? "border-transparent bg-primary text-primary-foreground" : "border-border bg-card/80 text-ink-2 hover:border-foreground/30 hover:text-foreground",
      )}
    >
      {children}
    </button>
  );
}

/** Clarifying questions as inline chips under the input. Unanswered = "not sure". */
export function InlineQuestions({ questions, onSubmit }: { questions: Question[]; onSubmit: (answers: Answer[]) => void }) {
  const { t, l } = useT();
  const [values, setValues] = useState<Record<string, Value>>({});
  const set = (id: string, v: Value) => setValues((p) => ({ ...p, [id]: v }));

  return (
    <form
      data-testid="question-form"
      className="fade-up border-t border-hairline bg-sun-soft/35 px-4 py-4 sm:px-5 dark:bg-sun-soft/25"
      onSubmit={(e) => {
        e.preventDefault();
        onSubmit(questions.map((q) => ({ fact_path: q.fact_path, value: values[q.id] ?? null })));
      }}
    >
      <p className="text-[15px] font-medium">{questions.length === 1 ? t("ask.title.one") : t("ask.title", { n: questions.length })}</p>
      <p className="mt-0.5 text-[12.5px] text-muted-foreground">{t("ask.lede")}</p>
      <ol className="mt-4 space-y-4">
        {questions.map((q, i) => {
          const val = values[q.id];
          const has = Object.prototype.hasOwnProperty.call(values, q.id);
          const opts = q.type === "boolean"
            ? [{ value: true, label: t("clarify.yes") }, { value: false, label: t("clarify.no") }]
            : q.options.map((o) => ({ value: o.value, label: l(o.label) }));
          const qid = `q-${q.id}`;
          return (
            <li key={q.id} data-testid="question" data-fact={q.fact_path}>
              <div className="flex items-start gap-2">
                <span className="num mt-px text-[12px] text-muted-foreground">{i + 1}.</span>
                <p id={qid} className="flex-1 text-[14px] leading-snug">
                  {l(q.text)}
                  <Tooltip>
                    <TooltipTrigger render={<button type="button" aria-label={`${t("ask.why")}: ${l(q.why)}`} className="ml-1 inline-flex translate-y-0.5 text-muted-foreground hover:text-foreground" />}>
                      <HelpCircle className="size-3.5" aria-hidden />
                    </TooltipTrigger>
                    <TooltipContent className="max-w-xs">{l(q.why)}</TooltipContent>
                  </Tooltip>
                </p>
              </div>
              {q.type === "text" ? (
                <input aria-labelledby={qid} value={typeof val === "string" ? val : ""} onChange={(e) => set(q.id, e.target.value || null)}
                  className="mt-2 ml-5 h-9 w-[calc(100%-1.25rem)] rounded-lg border border-input bg-card px-3 text-[13px] outline-none focus-visible:border-ring" />
              ) : opts.length > MAX_CHIPS ? (
                <select
                  aria-labelledby={qid}
                  value={!has || val === null ? "" : String(val)}
                  onChange={(e) => {
                    const hit = opts.find((o) => String(o.value) === e.target.value);
                    set(q.id, hit ? hit.value : null);
                  }}
                  className="mt-2 ml-5 h-10 w-[calc(100%-1.25rem)] max-w-full truncate rounded-xl border border-input bg-card px-3 text-[13px] outline-none focus-visible:border-ring"
                >
                  <option value="">{t("ask.notSure")}</option>
                  {opts.map((o) => <option key={String(o.value)} value={String(o.value)}>{o.label}</option>)}
                </select>
              ) : (
                <div role="radiogroup" aria-labelledby={qid} className="mt-2 ml-5 flex flex-wrap gap-1.5">
                  {opts.map((o) => (
                    <Chip key={String(o.value)} on={has && val === o.value} onClick={() => set(q.id, o.value)}>{o.label}</Chip>
                  ))}
                  <Chip on={has && val === null} onClick={() => set(q.id, null)}>{t("ask.notSure")}</Chip>
                </div>
              )}
            </li>
          );
        })}
      </ol>
      <div className="mt-5 flex justify-end">
        <button type="submit" data-testid="clarify-continue"
          className="inline-flex h-11 items-center gap-2 rounded-full bg-primary px-5 text-[14px] font-medium text-primary-foreground transition-opacity hover:opacity-90 max-sm:w-full max-sm:justify-center">
          {t("ask.submit")} <ArrowRight className="size-4" aria-hidden />
        </button>
      </div>
    </form>
  );
}
