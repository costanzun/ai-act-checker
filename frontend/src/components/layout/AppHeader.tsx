"use client";

import { Suspense } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { Menu, Moon, Sun } from "lucide-react";
import { useTheme } from "next-themes";
import { Button } from "@/components/ui/button";
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from "@/components/ui/dropdown-menu";
import { useT } from "@/i18n";
import { cn } from "@/lib/utils";

function LangToggle() {
  const { lang, setLang, t } = useT();
  return (
    <div role="group" aria-label={t("nav.language")} className="inline-flex rounded-md border border-border p-0.5">
      {(["en", "it"] as const).map((l) => (
        <button
          key={l}
          type="button"
          aria-pressed={lang === l}
          onClick={() => setLang(l)}
          className={cn(
            "rounded-[5px] px-2 py-1 text-xs font-medium tracking-wide transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring",
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
  return (
    <Button
      variant="ghost"
      size="icon"
      aria-label={t("nav.theme")}
      data-testid="theme-toggle"
      onClick={() => setTheme(resolvedTheme === "dark" ? "light" : "dark")}
    >
      <Sun className="hidden size-4 dark:block" aria-hidden />
      <Moon className="size-4 dark:hidden" aria-hidden />
    </Button>
  );
}

function useLinks() {
  const { t } = useT();
  return [
    { href: "/", label: t("nav.home") },
    { href: "/about", label: t("nav.about") },
  ];
}

function NavLinks() {
  const path = usePathname();
  const links = useLinks();
  return (
    <ul className="hidden items-center sm:flex">
      {links.map((l) => {
        const active = path === l.href;
        return (
          <li key={l.href}>
            <Link
              href={l.href}
              aria-current={active ? "page" : undefined}
              className={cn("rounded px-2 py-1.5 text-sm transition-colors hover:text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring",
                active ? "font-medium text-foreground underline decoration-eu decoration-2 underline-offset-8" : "text-muted-foreground")}
            >
              {l.label}
            </Link>
          </li>
        );
      })}
    </ul>
  );
}

function MobileMenu() {
  const { t } = useT();
  const links = useLinks();
  return (
    <DropdownMenu>
      <DropdownMenuTrigger render={<Button variant="ghost" size="icon" className="sm:hidden" aria-label={t("nav.menu")} data-testid="mobile-menu" />}>
        <Menu className="size-4" aria-hidden />
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end">
        {links.map((l) => (
          <DropdownMenuItem key={l.href} render={<Link href={l.href} />}>{l.label}</DropdownMenuItem>
        ))}
      </DropdownMenuContent>
    </DropdownMenu>
  );
}

export function AppHeader() {
  const { t } = useT();
  const links = useLinks();
  return (
    <header className="sticky top-0 z-40 border-b border-border bg-background">
      <a href="#main" className="sr-only focus:not-sr-only focus:absolute focus:left-4 focus:top-2 focus:z-50 focus:rounded focus:bg-primary focus:px-3 focus:py-1.5 focus:text-primary-foreground">
        {t("nav.skip")}
      </a>
      <div className="mx-auto flex h-14 max-w-6xl items-center justify-between gap-2 px-4 sm:px-6">
        <Link href="/" className="flex shrink-0 items-baseline gap-2 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring">
          <span aria-hidden className="inline-block size-2.5 translate-y-[-1px] rounded-full bg-eu" />
          <span className="whitespace-nowrap font-heading text-base font-semibold tracking-tight sm:text-lg">{t("app.name")}</span>
        </Link>
        <nav aria-label={t("nav.menu")} className="flex items-center gap-1 sm:gap-3">
          <Suspense fallback={<ul className="hidden items-center sm:flex">{links.map((l) => <li key={l.href} className="px-2 py-1.5 text-sm text-muted-foreground">{l.label}</li>)}</ul>}>
            <NavLinks />
          </Suspense>
          <LangToggle />
          <ThemeToggle />
          <MobileMenu />
        </nav>
      </div>
    </header>
  );
}
