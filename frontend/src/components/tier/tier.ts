import { Ban, CircleCheck, CircleMinus, Eye, TriangleAlert, type LucideIcon } from "lucide-react";
import type { DictKey } from "@/i18n/en";
import type { Tier } from "@/lib/types";
import type { SceneKey } from "@/components/pixel/sprites";

export const TIER_VAR: Record<Tier, string> = {
  prohibited: "var(--tier-prohibited)",
  high_risk: "var(--tier-high)",
  limited_risk: "var(--tier-limited)",
  minimal_risk: "var(--tier-minimal)",
  out_of_scope: "var(--tier-oos)",
};

/** Every tier carries an icon as well as a colour and a label. */
export const TIER_ICON: Record<Tier, LucideIcon> = {
  prohibited: Ban,
  high_risk: TriangleAlert,
  limited_risk: Eye,
  minimal_risk: CircleCheck,
  out_of_scope: CircleMinus,
};

export const TIER_KEY: Record<Tier, DictKey> = {
  prohibited: "tier.prohibited",
  high_risk: "tier.high_risk",
  limited_risk: "tier.limited_risk",
  minimal_risk: "tier.minimal_risk",
  out_of_scope: "tier.out_of_scope",
};

export const TIER_BLURB_KEY: Record<Tier, DictKey> = {
  prohibited: "tier.prohibited.blurb",
  high_risk: "tier.high_risk.blurb",
  limited_risk: "tier.limited_risk.blurb",
  minimal_risk: "tier.minimal_risk.blurb",
  out_of_scope: "tier.out_of_scope.blurb",
};

/** Flat colour block behind each verdict's dog. */
export const TIER_BLOCK: Record<Tier, string> = {
  prohibited: "var(--block-prohibited)",
  high_risk: "var(--block-high)",
  limited_risk: "var(--block-limited)",
  minimal_risk: "var(--block-minimal)",
  out_of_scope: "var(--block-oos)",
};

/** Which dog shows up for which verdict. */
export const TIER_SCENE: Record<Tier, SceneKey> = {
  prohibited: "prohibited",
  high_risk: "high_risk",
  limited_risk: "limited_risk",
  minimal_risk: "minimal_risk",
  out_of_scope: "out_of_scope",
};
