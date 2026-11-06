"use client";

import Link from "next/link";
import { useT } from "@/i18n";
import { useMeta } from "@/hooks/useMeta";

export function AppFooter() {
  const { t, formatDate } = useT();
  const { lawAsOf, checkedAt } = useMeta();
  return (
    <footer className="mt-10 border-t border-hairline">
      <div className="mx-auto flex max-w-5xl flex-col gap-2 px-4 py-6 text-[12px] text-muted-foreground sm:flex-row sm:items-center sm:justify-between sm:px-6">
        <p className="max-w-xl">{t("footer.notLegalAdvice")}</p>
        <p className="flex flex-wrap items-center gap-x-3 gap-y-1">
          <span>{t("footer.lawAsOf", { asOf: formatDate(lawAsOf), checked: formatDate(checkedAt) })}</span>
          <Link href="/about" className="underline-offset-4 hover:text-foreground hover:underline">{t("footer.method")}</Link>
        </p>
      </div>
    </footer>
  );
}
