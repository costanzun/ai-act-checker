"use client";

import { useT } from "@/i18n";
import type { DictKey } from "@/i18n/en";
import { cn } from "@/lib/utils";

const KEYS: Record<string, DictKey> = {
  gpai: "overlay.gpai",
  transparency_art50: "overlay.transparency_art50",
};

/** Neutral badge for additive overlays (GPAI obligations, Art. 50 duties); never replaces the tier colour. */
export function OverlayBadge({ overlay, className }: { overlay: string; className?: string }) {
  const { t } = useT();
  const key = KEYS[overlay];
  if (!key) return null;
  return (
    <span data-overlay={overlay} className={cn("inline-flex items-center rounded-full border border-dashed border-foreground/25 bg-card/60 px-2.5 py-0.5 text-[12px] font-medium whitespace-nowrap text-ink-2", className)}>
      {t(key)}
    </span>
  );
}
