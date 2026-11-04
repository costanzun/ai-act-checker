"use client";

import { useState, useSyncExternalStore } from "react";
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip";
import { useT } from "@/i18n";
import { citeLabel, fetchLawCached, snippet } from "@/lib/cite";
import { cn } from "@/lib/utils";
import { useCite } from "./CitationContext";

const HOVER_Q = "(hover: hover)";
function useCanHover(): boolean {
  return useSyncExternalStore(
    (cb) => { const m = window.matchMedia(HOVER_Q); m.addEventListener("change", cb); return () => m.removeEventListener("change", cb); },
    () => window.matchMedia(HOVER_Q).matches,
    () => true,
  );
}

/** Inline citation chip. Click opens the CitationPanel; hover shows the first 200 chars. */
export function Cite({ id, className }: { id: string; className?: string }) {
  const { lang, t } = useT();
  const { openCite } = useCite();
  const [preview, setPreview] = useState<string | null>(null);
  const [failed, setFailed] = useState(false);
  const label = citeLabel(id, lang);
  const canHover = useCanHover();

  const load = (open: boolean) => {
    if (!open || preview !== null || failed) return;
    fetchLawCached(id, lang)
      .then((r) => setPreview(snippet(r.full_text || r.provision.text)))
      .catch(() => setFailed(true));
  };

  const chipClass = cn(
    "mx-0.5 inline-flex items-center rounded-[5px] border border-eu/30 bg-eu/5 px-1.5 py-px align-baseline font-mono text-[0.78em] leading-snug text-eu transition-colors",
    "hover:border-eu hover:bg-eu/10 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring",
    className,
  );

  // Touch devices: tap opens the panel directly, no hover tooltip.
  if (!canHover) {
    return (
      <button type="button" data-cite={id} aria-label={t("cite.open", { label })} onClick={() => openCite(id)} className={chipClass}>
        {label}
      </button>
    );
  }

  return (
    <Tooltip onOpenChange={load}>
      <TooltipTrigger
        render={<button type="button" data-cite={id} aria-label={t("cite.open", { label })} onClick={() => openCite(id)} className={chipClass} />}
      >
        {label}
      </TooltipTrigger>
      <TooltipContent className="max-w-sm items-start text-left leading-relaxed">
        {failed ? t("cite.error") : (preview ?? t("cite.loading"))}
      </TooltipContent>
    </Tooltip>
  );
}
