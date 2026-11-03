"use client";

import { useState } from "react";
import { Copy, Download, FileText, Printer } from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { useT } from "@/i18n";
import { downloadBlob, exportMarkdown, exportPdf } from "@/lib/api";
import type { Assessment } from "@/lib/types";

export function ExportBar({ assessment }: { assessment: Assessment }) {
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

  return (
    <div className="no-print flex flex-wrap gap-2" role="group" aria-label="Export">
      <Button variant="outline" onClick={() => run("md")} disabled={busy !== null}><FileText aria-hidden /> {t("export.markdown")}</Button>
      <Button variant="outline" onClick={() => run("pdf")} disabled={busy !== null}><Download aria-hidden /> {t("export.pdf")}</Button>
      <Button variant="outline" onClick={() => window.print()}><Printer aria-hidden /> {t("export.print")}</Button>
      <Button variant="outline" onClick={copy}><Copy aria-hidden /> {t("export.link")}</Button>
    </div>
  );
}
