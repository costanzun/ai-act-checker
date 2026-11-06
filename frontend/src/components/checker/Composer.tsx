"use client";

import { useEffect, useRef, useState, type ReactNode } from "react";
import { ArrowRight } from "lucide-react";
import { useT } from "@/i18n";
import type { ExampleItem } from "@/lib/types";
import { cn } from "@/lib/utils";

export const MIN_CHARS = 20;
const SHOWN = 5;

interface Props {
  text: string;
  onText: (t: string) => void;
  onSubmit: (text: string) => void;
  examples: ExampleItem[];
  onExample: (ex: ExampleItem) => void;
  busy: boolean;
  /** Progress, inline questions or an error, rendered inside the same panel under the input. */
  children?: ReactNode;
}

/** The single input of the app: a text box, one-click examples and the primary button. */
export function Composer({ text, onText, onSubmit, examples, onExample, busy, children }: Props) {
  const { t } = useT();
  const ref = useRef<HTMLTextAreaElement>(null);
  const [all, setAll] = useState(false);
  const n = text.trim().length;
  const valid = n >= MIN_CHARS;
  const shown = all ? examples : examples.slice(0, SHOWN);

  // "/" anywhere outside a field jumps to the text box.
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key !== "/" || e.metaKey || e.ctrlKey || e.altKey) return;
      const el = e.target as HTMLElement | null;
      if (el && (el.tagName === "INPUT" || el.tagName === "TEXTAREA" || el.tagName === "SELECT" || el.isContentEditable)) return;
      e.preventDefault();
      ref.current?.focus();
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, []);

  const submit = () => { if (valid && !busy) onSubmit(text.trim()); };

  return (
    <section className="panel overflow-hidden" aria-labelledby="describe-label">
      <form
        className="p-5 sm:p-7"
        onSubmit={(e) => { e.preventDefault(); submit(); }}
      >
        <label id="describe-label" htmlFor="describe" className="h-section">{t("input.label")}</label>
        <textarea
          id="describe"
          ref={ref}
          value={text}
          onChange={(e) => onText(e.target.value)}
          onKeyDown={(e) => { if (e.key === "Enter" && (e.metaKey || e.ctrlKey)) { e.preventDefault(); submit(); } }}
          placeholder={t("input.placeholder")}
          rows={3}
          disabled={busy}
          className="mt-3 block min-h-28 w-full resize-y rounded-2xl border-2 border-input bg-card px-4 py-3.5 text-[16px] leading-relaxed outline-none transition-shadow placeholder:text-muted-foreground focus-visible:shadow-[0_0_0_4px_var(--sun)] disabled:opacity-70 sm:text-[17px]"
        />
        <div className="mt-3 flex flex-wrap items-center justify-between gap-3">
          <span className="text-[13px] font-medium text-muted-foreground" aria-live="polite">
            {!valid && n > 0 ? t("input.min", { n: MIN_CHARS - n }) : <span className="max-sm:hidden">{t("input.shortcut")}</span>}
          </span>
          <button
            type="submit"
            disabled={!valid || busy}
            data-testid="describe-submit"
            className="pill pill-primary h-13 px-7 text-[16px] max-sm:flex-1"
          >
            {t("input.submit")} <ArrowRight className="size-4" aria-hidden />
          </button>
        </div>
        {examples.length > 0 && !busy && (
          <div className="mt-5 flex flex-wrap items-center gap-2 border-t-2 border-dashed border-border pt-5" data-testid="examples">
            <span className="pixel-label mr-1 text-muted-foreground">{t("input.examples")}</span>
            {shown.map((ex) => (
              <button
                key={ex.id}
                type="button"
                data-testid="example-chip"
                data-example={ex.id}
                onClick={() => onExample(ex)}
                className="rounded-full border-2 border-foreground bg-card px-3.5 py-1.5 text-[13.5px] font-semibold transition-colors hover:bg-sun-soft"
              >
                {ex.title}
              </button>
            ))}
            {examples.length > SHOWN && (
              <button type="button" onClick={() => setAll((v) => !v)} aria-expanded={all}
                className={cn("rounded-full px-2.5 py-1.5 text-[13.5px] font-semibold underline underline-offset-4 hover:text-muted-foreground")}>
                {all ? "−" : t("input.more", { n: examples.length - SHOWN })}
              </button>
            )}
          </div>
        )}
      </form>
      {children}
    </section>
  );
}
