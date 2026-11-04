"use client";

import { createContext, useCallback, useContext, useEffect, useMemo, useState, type ReactNode } from "react";
import { en, type DictKey } from "./en";
import { it } from "./it";
import type { Lang, LText } from "@/lib/types";

const DICTS: Record<Lang, Record<DictKey, string>> = { en, it };
const STORAGE_KEY = "aiact.lang";

interface Ctx {
  lang: Lang;
  setLang: (l: Lang) => void;
  t: (key: DictKey, vars?: Record<string, string | number>) => string;
  /** Pick the current language from a {en, it} object, falling back to English. */
  l: (text: LText | undefined | null) => string;
  formatDate: (iso: string) => string;
  /** False until the language from ?lang= / localStorage has been resolved (children effects run first). */
  ready: boolean;
}

const LangContext = createContext<Ctx | null>(null);

function isLang(v: unknown): v is Lang {
  return v === "en" || v === "it";
}

export function LanguageProvider({ children }: { children: ReactNode }) {
  const [lang, setLangState] = useState<Lang>("en");
  const [ready, setReady] = useState(false);

  // Resolve initial language: ?lang= beats localStorage beats default.
  useEffect(() => {
    let next: Lang = "en";
    try {
      const fromUrl = new URLSearchParams(window.location.search).get("lang");
      const stored = window.localStorage.getItem(STORAGE_KEY);
      if (isLang(fromUrl)) next = fromUrl;
      else if (isLang(stored)) next = stored;
    } catch {
      /* storage unavailable */
    }
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setLangState(next);
    setReady(true);
  }, []);

  useEffect(() => {
    document.documentElement.lang = lang;
  }, [lang]);

  const setLang = useCallback((l: Lang) => {
    setLangState(l);
    try {
      window.localStorage.setItem(STORAGE_KEY, l);
      const url = new URL(window.location.href);
      url.searchParams.set("lang", l);
      window.history.replaceState(window.history.state, "", url.toString());
    } catch {
      /* ignore */
    }
  }, []);

  const value = useMemo<Ctx>(() => {
    const dict = DICTS[lang];
    const locale = lang === "it" ? "it-IT" : "en-GB";
    return {
      ready,
      lang,
      setLang,
      t: (key, vars) => {
        let s = dict[key] ?? en[key] ?? key;
        if (vars) for (const [k, v] of Object.entries(vars)) s = s.replaceAll(`{${k}}`, String(v));
        return s;
      },
      l: (text) => (text ? (text[lang] ?? text.en ?? Object.values(text)[0] ?? "") : ""),
      formatDate: (iso) => {
        const d = new Date(iso.length <= 10 ? `${iso}T00:00:00Z` : iso);
        if (Number.isNaN(d.getTime())) return iso;
        return d.toLocaleDateString(locale, { day: "numeric", month: "long", year: "numeric", timeZone: "UTC" });
      },
    };
  }, [lang, setLang, ready]);

  return <LangContext.Provider value={value}>{children}</LangContext.Provider>;
}

export function useT(): Ctx {
  const ctx = useContext(LangContext);
  if (!ctx) throw new Error("useT must be used within LanguageProvider");
  return ctx;
}
