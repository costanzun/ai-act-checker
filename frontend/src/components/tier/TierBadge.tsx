"use client";

import { useT } from "@/i18n";
import type { Tier } from "@/lib/types";
import { cn } from "@/lib/utils";
import { TIER_KEY, TIER_VAR } from "./tier";

export function TierBadge({ tier, className }: { tier: Tier; className?: string }) {
  const { t } = useT();
  const color = TIER_VAR[tier];
  return (
    <span
      data-tier={tier}
      className={cn("inline-flex items-center gap-1.5 rounded-full border px-2.5 py-0.5 text-xs font-medium whitespace-nowrap", className)}
      style={{ color, borderColor: `color-mix(in oklab, ${color} 45%, transparent)`, background: `color-mix(in oklab, ${color} 8%, transparent)` }}
    >
      <span aria-hidden className="size-1.5 rounded-full" style={{ background: color }} />
      {t(TIER_KEY[tier])}
    </span>
  );
}
