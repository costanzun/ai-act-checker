"use client";

import { useState } from "react";
import { ChevronDown } from "lucide-react";
import { CiteList, RichText } from "@/components/cite/RichText";
import { useT } from "@/i18n";
import type { Obligation, Role } from "@/lib/types";
import { cn } from "@/lib/utils";
import { isConditional, splitObligations } from "@/lib/verdict";

function Item({ o, n, note }: { o: Obligation; n?: number; note?: string }) {
  const { t, l, formatDate } = useT();
  return (
    <li className="flex gap-3 py-3.5" data-testid="obligation" data-priority={o.priority}>
      <span className={cn("num mt-0.5 flex size-7 shrink-0 items-center justify-center rounded-full text-[12.5px] font-bold",
        n !== undefined ? "bg-primary text-primary-foreground" : "border-2 border-border text-muted-foreground")}>
        {n !== undefined ? n : "·"}
      </span>
      <div className="min-w-0 flex-1">
        <div className="flex flex-wrap items-baseline gap-x-2 gap-y-0.5">
          <h3 className="text-[16px] font-bold leading-snug tracking-[-0.01em]">{l(o.title)}</h3>
          {o.applies_from && <span className="text-[12px] text-muted-foreground">{t("must.from", { date: formatDate(o.applies_from) })}</span>}
        </div>
        {note && <p className="pixel-label mt-1 text-muted-foreground">{note}</p>}
        <p className="mt-1 text-[14.5px] leading-relaxed text-ink-2"><RichText text={l(o.summary)} /></p>
        <div className="mt-1.5"><CiteList ids={o.citations} /></div>
      </div>
    </li>
  );
}

/** "What you must do": mandatory duties for the user's role, numbered; everything else one click away. */
export function MustDo({ obligations, role }: { obligations: Obligation[]; role: Role }) {
  const { t } = useT();
  const [open, setOpen] = useState(false);
  const { core, extra } = splitObligations(obligations, role);
  const noteFor = (o: Obligation) => {
    if (isConditional(o)) return t("obl.conditional");
    if (o.role !== "both" && role !== "unknown" && role !== "both" && o.role !== role) {
      return t("must.other", { role: t(o.role === "provider" ? "obl.role.provider" : "obl.role.deployer") });
    }
    return o.priority === "should" ? t("result.obligations.should") : undefined;
  };

  return (
    <section aria-labelledby="obligations-heading" data-testid="must-do" className="panel p-5 sm:p-7">
      <div className="flex flex-wrap items-baseline justify-between gap-2">
        <h2 id="obligations-heading" className="h-section">{t("must.title")}</h2>
        {obligations.length > 0 && (
          <span className="pixel-label text-muted-foreground" data-testid="obligations-count">
            {obligations.length === 1 ? t("must.count.one") : t("must.count", { n: obligations.length })}
          </span>
        )}
      </div>
      {obligations.length === 0 ? (
        <p className="mt-3 text-[14px] text-muted-foreground">{t("must.none")}</p>
      ) : (
        <>
          {core.length > 0 && <ol className="mt-2 divide-y divide-hairline">{core.map((o, i) => <Item key={o.id} o={o} n={i + 1} />)}</ol>}
          {extra.length > 0 && (
            <div className={cn(core.length > 0 && "mt-1 border-t border-hairline")}>
              <button
                type="button"
                aria-expanded={open}
                aria-controls="obligations-extra"
                onClick={() => setOpen((v) => !v)}
                data-testid="obligations-more"
                className="pill pill-secondary no-print mt-3 h-10 px-4 text-[13.5px]"
              >
                <ChevronDown className={cn("size-3.5 transition-transform", open && "rotate-180")} aria-hidden />
                {open ? t("must.less") : t("must.more", { n: extra.length })}
              </button>
              <ul id="obligations-extra" data-testid="conditional-group" className={cn("divide-y divide-hairline print:block", !open && "hidden")}>
                {extra.map((o) => <Item key={o.id} o={o} note={noteFor(o)} />)}
              </ul>
            </div>
          )}
        </>
      )}
    </section>
  );
}
