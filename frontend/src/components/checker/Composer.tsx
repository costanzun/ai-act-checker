"use client";

import { useEffect, useRef, useState, type ReactNode } from "react";
import { ArrowRight, Sparkles } from "lucide-react";
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
        className="p-4 sm:p-5"
        onSubmit={(e) => { e.preventDefault(); submit(); }}
      >
        <label id="describe-label" htmlFor="describe" className="text-[13px] font-medium text-muted-foreground">{t("input.label")}</label>
        <textarea
          id="describe"
          ref={ref}
          value={text}
          onChange={(e) => onText(e.target.value)}
          onKeyDown={(e) => { if (e.key === "Enter" && (e.metaKey || e.ctrlKey)) { e.preventDefault(); submit(); } }}
          placeholder={t("input.placeholder")}
          rows={3}
          disabled={busy}
          className="mt-2 block min-h-24 w-full resize-y rounded-xl border border-input bg-card/80 px-3.5 py-3 text-[15px] leading-relaxed outline-none transition-colors placeholder:text-muted-foreground/80 focus-visible:border-ring focus-visible:ring-3 focus-visible:ring-ring/30 disabled:opacity-70 sm:text-[16px]"
        />
        <div className="mt-3 flex flex-wrap items-center justify-between gap-3">
          <span className="text-[12px] text-muted-foreground" aria-live="polite">
            {!valid && n > 0 ? t("input.min", { n: MIN_CHARS - n }) : <span className="max-sm:hidden">{t("input.shortcut")}</span>}
          </span>
          <button
            type="submit"
            disabled={!valid || busy}
            data-testid="describe-submit"
            className="inline-flex h-11 items-center gap-2 rounded-full bg-primary px-5 text-[14px] font-medium text-primary-foreground transition-opacity hover:opacity-90 disabled:opacity-40 max-sm:flex-1 max-sm:justify-center"
          >
            {t("input.submit")} <ArrowRight className="size-4" aria-hidden />
          </button>
        </div>
        {examples.length > 0 && !busy && (
          <div className="mt-4 flex flex-wrap items-center gap-1.5 border-t border-dashed border-border pt-4" data-testid="examples">
            <span className="mr-1 inline-flex items-center gap-1 text-[12px] text-muted-foreground">
              <Sparkles className="size-3.5 text-brand" aria-hidden /> {t("input.examples")}
            </span>
            {shown.map((ex) => (
              <button
                key={ex.id}
                type="button"
                data-testid="example-chip"
                data-example={ex.id}
                onClick={() => onExample(ex)}
                className="rounded-full border border-border bg-card/70 px-3 py-1 text-[12.5px] text-ink-2 transition-colors hover:border-foreground/30 hover:bg-card hover:text-foreground"
              >
                {ex.title}
              </button>
            ))}
            {examples.length > SHOWN && (
              <button type="button" onClick={() => setAll((v) => !v)} aria-expanded={all}
                className={cn("rounded-full px-2.5 py-1 text-[12.5px] text-muted-foreground underline-offset-4 hover:text-foreground hover:underline")}>
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
