"use client";

import { useState } from "react";
import { Copy, Download, FileText, Printer } from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { useT } from "@/i18n";
import { cn } from "@/lib/utils";
import { downloadBlob, exportMarkdown, exportPdf } from "@/lib/api";
import type { Assessment } from "@/lib/types";

export function ExportBar({ assessment, className }: { assessment: Assessment; className?: string }) {
  const { t } = useT();
  const [busy, setBusy] = useState<"md" | "pdf" | null>(null);

  const run = async (kind: "md" | "pdf") => {
    setBusy(kind);
    try {
      if (kind === "md") downloadBlob(await exportMarkdown(assessment), `ai-act-assessment-${assessment.id}.md`);
      else {
        const blob = await exportPdf(assessment);
        if (blob) downloadBlob(blob, `ai-act-assessment-${assessment.id}.pdf`);
        else window.print();
      }
    } catch {
      toast.error(t("export.failed"));
    } finally {
      setBusy(null);
    }
  };

  const copy = async () => {
    try {
      const url = new URL(window.location.href);
      url.hash = "";
      url.searchParams.delete("q");
      url.searchParams.delete("example");
      url.searchParams.set("id", assessment.id);
      await navigator.clipboard.writeText(url.toString());
      toast.success(t("export.copied"), { description: t("export.linkNote") });
    } catch {
      toast.error(t("export.failed"));
    }
  };

  const btn = "max-sm:px-2.5";
  const lbl = "hidden sm:inline";
  return (
    <div className={cn("no-print flex flex-nowrap gap-2", className)} role="group" aria-label={t("export.label")}>
      <Button variant="outline" className={btn} title={t("export.markdown")} aria-label={t("export.markdown")} onClick={() => run("md")} disabled={busy !== null}><FileText aria-hidden /><span className={lbl}>{t("export.markdown")}</span></Button>
      <Button variant="outline" className={btn} title={t("export.pdf")} aria-label={t("export.pdf")} onClick={() => run("pdf")} disabled={busy !== null}><Download aria-hidden /><span className={lbl}>{t("export.pdf")}</span></Button>
      <Button variant="outline" className={btn} title={t("export.print")} aria-label={t("export.print")} onClick={() => window.print()}><Printer aria-hidden /><span className={lbl}>{t("export.print")}</span></Button>
      <Button variant="outline" className={btn} title={t("export.link")} aria-label={t("export.link")} onClick={copy}><Copy aria-hidden /><span className={lbl}>{t("export.link")}</span></Button>
    </div>
  );
}
