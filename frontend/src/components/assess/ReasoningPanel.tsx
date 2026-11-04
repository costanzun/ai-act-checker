"use client";

import ReactMarkdown from "react-markdown";
import { Cite } from "@/components/cite/Cite";
import { useT } from "@/i18n";
import { CITE_TOKEN, safeStreamText } from "@/lib/cite";

const PREFIX = "cite://";

/** Renders reasoning_md; [[art:6.2]] tokens become <Cite> chips. Safe to call with partial streamed text. */
const SAFE_URL = /^(https?:|mailto:|#)/i;

export function ReasoningPanel({ markdown, streaming = false, note }: { markdown: string; streaming?: boolean; note?: string }) {
  const { t } = useT();
  const safe = streaming ? safeStreamText(markdown) : markdown;
  const md = safe.replace(CITE_TOKEN, (_m, id: string) => `[${id}](${PREFIX}${id})`);
  return (
    <section aria-labelledby="reasoning-heading" aria-busy={streaming} data-testid="reasoning-panel">
      <h2 id="reasoning-heading" className="font-heading text-2xl font-medium">
        {t("result.reasoning")}
        {streaming && <span className="ml-3 align-middle text-xs font-normal text-muted-foreground shimmer-text">{t("result.reasoning.streaming")}</span>}
      </h2>
      {note && <p className="mt-1 text-xs text-muted-foreground" data-testid="regenerated-note">{note}</p>}
      <div className="prose-legal mt-4 max-w-3xl text-[1.02rem]">
        <ReactMarkdown
          skipHtml
          disallowedElements={["img", "script", "iframe", "style"]}
          urlTransform={(u) => (u.startsWith(PREFIX) || SAFE_URL.test(u) ? u : "")}
          components={{
            a: ({ href, children }) =>
              href?.startsWith(PREFIX) ? <Cite id={href.slice(PREFIX.length)} /> : (
                <a href={href} target="_blank" rel="noopener noreferrer" className="text-eu underline underline-offset-2">{children}</a>
              ),
          }}
        >
          {md}
        </ReactMarkdown>
        {streaming && <span aria-hidden className="inline-block h-4 w-0.5 animate-pulse bg-foreground align-middle" />}
      </div>
    </section>
  );
}
