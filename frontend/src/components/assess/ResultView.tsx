"use client";

import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Separator } from "@/components/ui/separator";
import { TierHero } from "@/components/tier/TierHero";
import { useT } from "@/i18n";
import type { Assessment } from "@/lib/types";
import { Checklist } from "./Checklist";
import { ExportBar } from "./ExportBar";
import { FindingsList } from "./FindingsList";
import { ObligationsTabs } from "./ObligationsTabs";
import { ReasoningPanel } from "./ReasoningPanel";
import { RelatedProvisions } from "./RelatedProvisions";
import { TimelineStrip } from "./TimelineStrip";
import { UncertaintiesCallout } from "./UncertaintiesCallout";
import { Info } from "lucide-react";

export function ResultView({ assessment, canAskAgain, onAskAgain }: { assessment: Assessment; canAskAgain: boolean; onAskAgain: () => void }) {
  const { t, l } = useT();
  const c = assessment.classification;
  return (
    <div className="print-expand space-y-10" data-testid="result-view">
      <TierHero assessment={assessment} />
      <ExportBar assessment={assessment} />
      <UncertaintiesCallout assessment={assessment} canAskAgain={canAskAgain} onAskAgain={onAskAgain} />
      <ReasoningPanel markdown={assessment.reasoning_md} />
      <Separator />
      <FindingsList findings={c.findings} />
      <ObligationsTabs obligations={assessment.obligations} role={c.role} />
      <Checklist assessmentId={assessment.id} items={assessment.checklist} />
      <TimelineStrip relevant={c.applies_from} />
      <RelatedProvisions items={assessment.related_provisions} />
      <Alert>
        <Info aria-hidden />
        <AlertTitle>{t("result.disclaimer.title")}</AlertTitle>
        <AlertDescription>{l(assessment.disclaimer)}</AlertDescription>
      </Alert>
      <p className="font-mono text-xs text-muted-foreground">
        {t("result.metrics", { model: `${assessment.model.provider} / ${assessment.model.model}`, secs: (assessment.metrics.latency_ms / 1000).toFixed(1) })}
        {assessment.metrics.cost_usd > 0 && ` · ${t("result.metrics.cost", { cost: assessment.metrics.cost_usd.toFixed(3) })}`}
      </p>
    </div>
  );
}
