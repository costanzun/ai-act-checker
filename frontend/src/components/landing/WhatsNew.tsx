"use client";

import Link from "next/link";
import { CalendarClock } from "lucide-react";
import { useT } from "@/i18n";

export function WhatsNew() {
  const { t, formatDate } = useT();
  return (
    <aside aria-labelledby="new-heading" className="border-t border-border py-12">
      <div className="flex gap-4 rounded-lg border border-border bg-card p-5 sm:p-6">
        <CalendarClock className="mt-1 size-5 shrink-0 text-eu" aria-hidden />
        <div>
          <h2 id="new-heading" className="font-heading text-xl font-medium">{t("landing.new.title")}</h2>
          <p className="mt-2 max-w-3xl text-sm leading-relaxed text-muted-foreground">
            {t("landing.new.text", { d1: formatDate("2027-12-02"), d2: formatDate("2028-08-02") })}
          </p>
          <Link href="/about" className="mt-3 inline-block text-sm font-medium text-eu underline-offset-4 hover:underline">{t("landing.new.link")}</Link>
        </div>
      </div>
    </aside>
  );
}
