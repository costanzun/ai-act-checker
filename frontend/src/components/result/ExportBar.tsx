"use client";

import { useState } from "react";
import { Download, FileText, Link2 } from "lucide-react";
import { toast } from "sonner";
import { useT } from "@/i18n";
import { downloadBlob, exportMarkdown, exportPdf } from "@/lib/api";
import type { Assessment } from "@/lib/types";
import { cn } from "@/lib/utils";

const pill = "pill h-12 px-5 text-[14.5px]";

/** One-click exports and a shareable link. The PDF and Markdown are built by the backend. */
export function ExportBar({ assessment, className }: { assessment: Assessment; className?: string }) {
  const { t, lang } = useT();
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
      const url = new URL("/", window.location.origin);
      url.searchParams.set("id", assessment.id);
      url.searchParams.set("lang", lang);
      await navigator.clipboard.writeText(url.toString());
      toast.success(t("export.copied"), { description: t("export.linkNote") });
    } catch {
      toast.error(t("export.failed"));
    }
  };

  return (
    <div className={cn("no-print grid grid-cols-2 gap-2 sm:flex sm:flex-wrap", className)} role="group" aria-label={t("export.label")}>
      <button type="button" className={cn(pill, "pill-primary col-span-2 sm:min-w-44")} aria-label={t("export.pdf")} onClick={() => run("pdf")} disabled={busy !== null}>
        <Download className="size-4" aria-hidden /> {t("export.pdfShort")}
      </button>
      <button type="button" className={cn(pill, "pill-secondary")} aria-label={t("export.markdown")} onClick={() => run("md")} disabled={busy !== null}>
        <FileText className="size-4" aria-hidden /> Markdown
      </button>
      <button type="button" className={cn(pill, "pill-secondary")} aria-label={t("export.link")} onClick={copy}>
        <Link2 className="size-4" aria-hidden /> <span>{t("export.linkShort")}</span>
      </button>
    </div>
  );
}
