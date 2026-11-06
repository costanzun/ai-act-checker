"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { Moon, Sun } from "lucide-react";
import { DogScene } from "@/components/pixel/Pixel";
import { ModelPicker } from "@/components/layout/ModelPicker";
import { useTheme } from "next-themes";
import { useT } from "@/i18n";
import { cn } from "@/lib/utils";

function LangToggle() {
  const { lang, setLang, t } = useT();
  return (
    <div role="group" aria-label={t("nav.language")} className="inline-flex h-10 items-center rounded-full border-2 border-foreground bg-card p-0.5">
      {(["en", "it"] as const).map((l) => (
        <button
          key={l}
          type="button"
          aria-pressed={lang === l}
          onClick={() => setLang(l)}
          className={cn(
            "h-full rounded-full px-3 text-[12.5px] font-bold tracking-wide transition-colors",
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
      className="inline-flex size-10 items-center justify-center rounded-full border-2 border-foreground bg-card text-foreground transition-colors hover:bg-sun-soft"
    >
      {dark ? <Sun className="size-4" aria-hidden /> : <Moon className="size-4" aria-hidden />}
    </button>
  );
}

export function AppHeader() {
  const { t, lang } = useT();
  return (
    <header className="sticky top-0 z-40 bg-[var(--page-header)]">
      <a href="#main" className="sr-only focus:not-sr-only focus:absolute focus:left-4 focus:top-2 focus:z-50 focus:rounded focus:bg-primary focus:px-3 focus:py-1.5 focus:text-primary-foreground">
        {t("nav.skip")}
      </a>
      <div className="mx-auto flex h-16 max-w-5xl items-center justify-between gap-2 px-4 sm:px-6">
        <Link href={`/?lang=${lang}`} className="flex min-w-0 items-center gap-2">
          <span aria-hidden className="flex size-10 shrink-0 items-center justify-center overflow-hidden rounded-full bg-[#18A0F0]">
            <DogScene scene="logo" className="mt-2 w-9" />
          </span>
          <span className="truncate text-[17px] font-black tracking-[-0.04em]">{t("app.name")}</span>
        </Link>
        <div className="flex shrink-0 items-center gap-1.5">
          <ModelPicker />
          <LangToggle />
          <ThemeToggle />
        </div>
      </div>
    </header>
  );
}
