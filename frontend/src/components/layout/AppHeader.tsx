"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { Moon, Scale, Sun } from "lucide-react";
import { useTheme } from "next-themes";
import { useT } from "@/i18n";
import { cn } from "@/lib/utils";

function LangToggle() {
  const { lang, setLang, t } = useT();
  return (
    <div role="group" aria-label={t("nav.language")} className="inline-flex h-9 items-center rounded-xl border border-hairline bg-card/70 p-0.5">
      {(["en", "it"] as const).map((l) => (
        <button
          key={l}
          type="button"
          aria-pressed={lang === l}
          onClick={() => setLang(l)}
          className={cn(
            "h-full rounded-[9px] px-2.5 text-[12px] font-medium tracking-wide transition-colors",
            lang === l ? "bg-primary text-primary-foreground" : "text-muted-foreground hover:text-foreground",
          )}
        >
          {l.toUpperCase()}
        </button>
      ))}
    </div>
  );
}

function ThemeToggle() {
  const { t } = useT();
  const { resolvedTheme, setTheme } = useTheme();
  const [mounted, setMounted] = useState(false);
  // eslint-disable-next-line react-hooks/set-state-in-effect
  useEffect(() => setMounted(true), []);
  const dark = mounted && resolvedTheme === "dark";
  return (
    <button
      type="button"
      aria-label={t("nav.theme")}
      data-testid="theme-toggle"
      onClick={() => setTheme(dark ? "light" : "dark")}
      className="inline-flex size-9 items-center justify-center rounded-xl border border-hairline bg-card/70 text-muted-foreground transition-colors hover:text-foreground"
    >
      {dark ? <Sun className="size-4" aria-hidden /> : <Moon className="size-4" aria-hidden />}
    </button>
  );
}

export function AppHeader() {
  const { t, lang } = useT();
  return (
    <header className="sticky top-0 z-40 border-b border-hairline bg-background/80 backdrop-blur-md">
      <a href="#main" className="sr-only focus:not-sr-only focus:absolute focus:left-4 focus:top-2 focus:z-50 focus:rounded focus:bg-primary focus:px-3 focus:py-1.5 focus:text-primary-foreground">
        {t("nav.skip")}
      </a>
      <div className="mx-auto flex h-14 max-w-5xl items-center justify-between gap-2 px-4 sm:px-6">
        <Link href={`/?lang=${lang}`} className="flex min-w-0 items-center gap-2">
          <span aria-hidden className="flex size-7 shrink-0 items-center justify-center rounded-lg bg-sun text-[#1C1B18]">
            <Scale className="size-4" strokeWidth={2} />
          </span>
          <span className="truncate text-[15px] font-medium tracking-tight">{t("app.name")}</span>
        </Link>
        <div className="flex items-center gap-1.5">
          <LangToggle />
          <ThemeToggle />
        </div>
      </div>
    </header>
  );
}
