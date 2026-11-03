import type { DictKey } from "@/i18n/en";
import type { Tier } from "@/lib/types";

export const TIER_VAR: Record<Tier, string> = {
  prohibited: "var(--tier-prohibited)",
  high_risk: "var(--tier-high)",
  limited_risk: "var(--tier-limited)",
  minimal_risk: "var(--tier-minimal)",
  out_of_scope: "var(--tier-oos)",
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
