"use client";

import { useState } from "react";
import { ArrowRight, HelpCircle } from "lucide-react";
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip";
import { DogScene } from "@/components/pixel/Pixel";
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
        "min-h-10 rounded-full border-2 px-4 py-1.5 text-left text-[14px] font-semibold leading-snug transition-colors",
        on ? "border-primary bg-primary text-primary-foreground" : "border-foreground bg-card hover:bg-sun-soft",
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
      className="fade-up px-2 pb-2 sm:px-2.5 sm:pb-2.5"
      onSubmit={(e) => {
        e.preventDefault();
        onSubmit(questions.map((q) => ({ fact_path: q.fact_path, value: values[q.id] ?? null })));
      }}
    >
      <div className="px-block flex flex-col gap-3 overflow-hidden rounded-[1.4rem] px-5 pt-5 sm:flex-row sm:items-end sm:gap-6 sm:px-7"
        style={{ "--block": "var(--block-questions)", "--grid": "5px" } as React.CSSProperties}>
        <div className="min-w-0 flex-1 sm:pb-6">
          <p className="pixel-label">{t("ask.eyebrow")}</p>
          <p className="display mt-2 text-balance text-[30px] sm:text-[40px]">{questions.length === 1 ? t("ask.title.one") : t("ask.title", { n: questions.length })}</p>
          <p className="mt-2 text-[14.5px] font-medium">{t("ask.lede")}</p>
        </div>
        <DogScene scene="questions" label={t("scene.questions")} className="w-[230px] shrink-0 max-sm:mx-auto sm:w-[270px]" />
      </div>
      <ol className="mt-5 space-y-5 px-3 sm:px-5">
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
                <span className="pixel-label mt-1 text-muted-foreground">{i + 1}.</span>
                <p id={qid} className="flex-1 text-[16px] font-semibold leading-snug">
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
                  className="mt-2.5 ml-5 h-11 w-[calc(100%-1.25rem)] rounded-xl border-2 border-input bg-card px-3 text-[14px] outline-none focus-visible:shadow-[0_0_0_4px_var(--sun)]" />
              ) : opts.length > MAX_CHIPS ? (
                <select
                  aria-labelledby={qid}
                  value={!has || val === null ? "" : String(val)}
                  onChange={(e) => {
                    const hit = opts.find((o) => String(o.value) === e.target.value);
                    set(q.id, hit ? hit.value : null);
                  }}
                  className="mt-2.5 ml-5 h-11 w-[calc(100%-1.25rem)] max-w-full truncate rounded-xl border-2 border-input bg-card px-3 text-[14px] font-medium outline-none focus-visible:shadow-[0_0_0_4px_var(--sun)]"
                >
                  <option value="">{t("ask.notSure")}</option>
                  {opts.map((o) => <option key={String(o.value)} value={String(o.value)}>{o.label}</option>)}
                </select>
              ) : (
                <div role="radiogroup" aria-labelledby={qid} className="mt-2.5 ml-5 flex flex-wrap gap-2">
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
      <div className="mt-6 flex justify-end px-3 pb-3 sm:px-5 sm:pb-4">
        <button type="submit" data-testid="clarify-continue"
          className="pill pill-primary h-13 px-7 text-[16px] max-sm:w-full">
          {t("ask.submit")} <ArrowRight className="size-4" aria-hidden />
        </button>
      </div>
    </form>
  );
}
