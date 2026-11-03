"use client";

import { AlertTriangle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { useT } from "@/i18n";

export type FlowError = { code: "network" | "llm_unavailable" | "invalid_input" | "internal"; message?: string };

export function ErrorCard({ error, onRetry, onEdit }: { error: FlowError; onRetry: () => void; onEdit: () => void }) {
  const { t } = useT();
  return (
    <Card role="alert" data-testid="error-card" className="border-l-4 border-l-[color:var(--tier-prohibited)]">
      <CardContent className="space-y-3">
        <h2 className="flex items-center gap-2 font-heading text-2xl font-medium"><AlertTriangle className="size-5 text-[color:var(--tier-prohibited)]" aria-hidden /> {t("error.title")}</h2>
        <p className="text-sm text-muted-foreground">{error.message || t(`error.${error.code}` as const)}</p>
        <div className="flex flex-wrap gap-2">
          <Button onClick={onRetry}>{t("error.retry")}</Button>
          <Button variant="outline" onClick={onEdit}>{t("error.back")}</Button>
        </div>
      </CardContent>
    </Card>
  );
}
