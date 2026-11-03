import type { Lang, LawResponse } from "./types";
import { getLaw } from "./api";

export const CITE_TOKEN = /\[\[([a-z]+:[A-Za-z0-9.\-_]+)\]\]/g;

/** Human label for a provision ID without a network call (EN/IT), e.g. art:6.3.a -> "Art. 6(3)(a)". */
export function citeLabel(id: string, lang: Lang): string {
  const [kind, rest = ""] = id.split(":");
  const parts = rest.split(".");
  if (kind === "art") {
    const [n, p, ...pts] = parts;
    if (lang === "it") {
      let s = `Art. ${n}`;
      if (p) s += `, par. ${p}`;
      if (pts.length) s += `, lett. ${pts[0]})${pts.slice(1).map((x) => `(${x})`).join("")}`;
      return s;
    }
    return `Art. ${n}${p ? `(${p})` : ""}${pts.map((x) => `(${x})`).join("")}`;
  }
  if (kind === "annex") {
    const [n, ...r] = parts;
    const word = lang === "it" ? "Allegato" : "Annex";
    if (!r.length) return `${word} ${n}`;
    if (/^[A-Z]$/.test(r[0]) && n === "I") return `${word} ${n}, ${lang === "it" ? "sezione" : "Section"} ${r[0]}${r[1] ? `, ${lang === "it" ? "punto" : "point"} ${r[1]}` : ""}`;
    const [pt, ...sub] = r;
    return `${word} ${n}, ${lang === "it" ? "punto" : "point"} ${pt}${sub.length ? (lang === "it" ? `, lett. ${sub[0]})` : `(${sub[0]})`) : ""}`;
  }
  if (kind === "rec") return `${lang === "it" ? "Considerando" : "Recital"} ${parts[0]}`;
  if (kind === "guid") return lang === "it" ? "Orientamenti" : "Guidance";
  return id;
}

const cache = new Map<string, Promise<LawResponse>>();

/** Module-level cache so tooltips, panel and law page share one fetch per (id, lang). */
export function fetchLawCached(id: string, lang: Lang): Promise<LawResponse> {
  const key = `${lang}:${id}`;
  let p = cache.get(key);
  if (!p) {
    p = getLaw(id, lang);
    p.catch(() => cache.delete(key));
    cache.set(key, p);
  }
  return p;
}

export function snippet(text: string, max = 200): string {
  const clean = text.replace(/\s+/g, " ").trim();
  return clean.length > max ? `${clean.slice(0, max).trimEnd()}…` : clean;
}

/** Hold back an unterminated "[[..." suffix while streaming so half tokens never render. */
export function safeStreamText(text: string): string {
  const i = text.lastIndexOf("[[");
  if (i !== -1 && !text.slice(i).includes("]]")) return text.slice(0, i);
  return text;
}
