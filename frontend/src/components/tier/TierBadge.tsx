"use client";

import { useT } from "@/i18n";
import type { Tier } from "@/lib/types";
import { cn } from "@/lib/utils";
import { TIER_ICON, TIER_KEY, TIER_VAR } from "./tier";

/** Small tier pill: icon + label + colour. */
export function TierBadge({ tier, className }: { tier: Tier; className?: string }) {
  const { t } = useT();
  const color = TIER_VAR[tier];
  const Icon = TIER_ICON[tier];
  return (
    <span
      data-tier={tier}
      className={cn("inline-flex items-center gap-1 rounded-full border-2 px-2.5 py-0.5 text-[12.5px] font-bold whitespace-nowrap", className)}
      style={{ color, borderColor: color, background: "var(--card)" }}
    >
      <Icon className="size-3.5" aria-hidden strokeWidth={2} />
      {t(TIER_KEY[tier])}
    </span>
  );
}
