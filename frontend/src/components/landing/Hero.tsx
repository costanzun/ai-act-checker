"use client";

import { useRouter } from "next/navigation";
import { useEffect, useRef, useState } from "react";
import { ArrowRight } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { useT } from "@/i18n";

export function Hero() {
  const { t, lang } = useT();
  const router = useRouter();
  const [text, setText] = useState("");
  const ref = useRef<HTMLTextAreaElement>(null);

  // Press "/" anywhere (outside a field) to jump to the textarea.
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key !== "/" || e.metaKey || e.ctrlKey || e.altKey) return;
      const el = e.target as HTMLElement | null;
      if (el && (el.tagName === "INPUT" || el.tagName === "TEXTAREA" || el.isContentEditable)) return;
      e.preventDefault();
      ref.current?.focus();
      ref.current?.scrollIntoView({ block: "center" });
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, []);

  const submit = (e: React.FormEvent) => {
    e.preventDefault();
    const q = text.trim();
    if (!q) { ref.current?.focus(); return; }
    router.push(q ? `/assess?lang=${lang}&q=${encodeURIComponent(q)}` : `/assess?lang=${lang}`);
  };

  return (
    <section className="grid gap-10 pt-12 pb-10 md:pt-16 lg:grid-cols-[1.1fr_1fr] lg:items-start lg:gap-14">
      <div>
        <p className="font-mono text-xs uppercase tracking-[0.16em] text-eu">{t("landing.eyebrow")}</p>
        <h1 className="mt-4 font-heading text-4xl font-medium leading-[1.1] sm:text-5xl lg:text-[3.25rem]">{t("landing.title")}</h1>
        <div className="rule mt-6 w-16 border-t-2 border-eu" aria-hidden />
        <p className="mt-6 max-w-xl text-base leading-relaxed text-muted-foreground sm:text-lg">{t("landing.lede")}</p>
      </div>
      <Card className="border-border shadow-none ring-0 border">
        <CardContent>
          <form onSubmit={submit} className="space-y-3">
            <Label htmlFor="hero-description" className="font-heading text-xl font-medium">{t("landing.card.title")}</Label>
            <p id="hero-hint" className="text-sm text-muted-foreground">{t("landing.card.hint")}</p>
            <Textarea
              id="hero-description"
              ref={ref}
              aria-describedby="hero-hint"
              value={text}
              onChange={(e) => setText(e.target.value)}
              placeholder={t("landing.card.placeholder")}
              rows={5}
              className="min-h-32 resize-y bg-background text-base"
            />
            <Button type="submit" size="lg" className="w-full sm:w-auto" data-testid="hero-submit">
              {t("landing.card.cta")} <ArrowRight className="size-4" aria-hidden />
            </Button>
            <p className="text-xs text-muted-foreground no-print">{t("landing.card.shortcut")}</p>
          </form>
        </CardContent>
      </Card>
    </section>
  );
}
