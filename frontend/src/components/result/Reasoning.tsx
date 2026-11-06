"use client";

import { useState } from "react";
import ReactMarkdown from "react-markdown";
import { ChevronDown } from "lucide-react";
import { Cite } from "@/components/cite/Cite";
import { useT } from "@/i18n";
import { CITE_TOKEN, safeStreamText } from "@/lib/cite";
import { cn } from "@/lib/utils";

const PREFIX = "cite://";
const SAFE_URL = /^(https?:|mailto:|#)/i;

/** Renders reasoning_md; [[art:6.2]] tokens become <Cite> chips. Safe with partial streamed text. */
export function ReasoningBody({ markdown, streaming = false }: { markdown: string; streaming?: boolean }) {
  const safe = streaming ? safeStreamText(markdown) : markdown;
  const md = safe.replace(CITE_TOKEN, (_m, id: string) => `[${id}](${PREFIX}${id})`);
  return (
    <div className="prose-legal max-w-3xl text-[14.5px]" data-testid="reasoning-panel" aria-busy={streaming}>
      <ReactMarkdown
        skipHtml
        disallowedElements={["img", "script", "iframe", "style"]}
        urlTransform={(u) => (u.startsWith(PREFIX) || SAFE_URL.test(u) ? u : "")}
        components={{
          a: ({ href, children }) =>
            href?.startsWith(PREFIX) ? <Cite id={href.slice(PREFIX.length)} /> : (
              <a href={href} target="_blank" rel="noopener noreferrer" className="text-brand underline underline-offset-2">{children}</a>
            ),
        }}
      >
        {md}
      </ReactMarkdown>
      {streaming && <span aria-hidden className="inline-block h-4 w-0.5 animate-pulse bg-foreground align-middle" />}
    </div>
  );
}

/** The model-written narrative, collapsed by default: the verdict and lists above are the answer. */
export function Reasoning({ markdown, streaming, note, metrics }: { markdown: string; streaming: boolean; note?: string; metrics?: string }) {
  const { t } = useT();
  const [open, setOpen] = useState(false);
  return (
    <section aria-labelledby="reasoning-heading" className="panel p-5 sm:p-7" data-testid="reasoning">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <h2 id="reasoning-heading" className="h-section">
          {t("reasoning.title")}
          {streaming && <span className="pixel-label ml-2.5 align-middle text-muted-foreground shimmer-text" data-testid="reasoning-streaming">{t("reasoning.writing")}</span>}
        </h2>
        <button
          type="button"
          aria-expanded={open}
          aria-controls="reasoning-body"
          onClick={() => setOpen((v) => !v)}
          data-testid="reasoning-toggle"
          className="pill pill-secondary no-print h-10 px-4 text-[13.5px]"
        >
          <ChevronDown className={cn("size-3.5 transition-transform", open && "rotate-180")} aria-hidden />
          {open ? t("reasoning.hide") : t("reasoning.show")}
        </button>
      </div>
      <div id="reasoning-body" className={cn("mt-4 print:block", !open && "hidden")}>
        {note && <p className="mb-2 text-[12px] text-muted-foreground" data-testid="regenerated-note">{note}</p>}
        {markdown ? <ReasoningBody markdown={markdown} streaming={streaming} /> : <p className="text-[13px] text-muted-foreground shimmer-text">{t("progress.writing")}</p>}
        {metrics && <p className="num mt-4 text-[11.5px] text-muted-foreground">{metrics}</p>}
      </div>
    </section>
  );
}
