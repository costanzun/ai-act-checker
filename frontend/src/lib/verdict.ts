import type { Assessment, Milestone, Obligation, Role } from "./types";

/**
 * The one date that matters for this result: the earliest milestone still ahead of us,
 * otherwise the most recent one already in force. Out-of-scope results have none.
 */
export function keyDeadline(a: Assessment, today = new Date()): Milestone | null {
  const ms = [...a.classification.applies_from].sort((x, y) => x.date.localeCompare(y.date));
  if (!ms.length || a.classification.tier === "out_of_scope") return null;
  const iso = today.toISOString().slice(0, 10);
  return ms.find((m) => m.date > iso) ?? ms[ms.length - 1];
}

/** Whole months (or days, under a month) from today to an ISO date; negative when past. */
export function until(date: string, today = new Date()): { months: number; days: number } {
  const d = new Date(`${date}T00:00:00Z`);
  const days = Math.round((d.getTime() - Date.UTC(today.getUTCFullYear(), today.getUTCMonth(), today.getUTCDate())) / 86_400_000);
  const months = (d.getUTCFullYear() - today.getUTCFullYear()) * 12 + (d.getUTCMonth() - today.getUTCMonth()) - (d.getUTCDate() < today.getUTCDate() ? 1 : 0);
  return { months, days };
}

const ABBREV = /\b(?:Art|Arts|art|artt|par|lett|No|no|n|p|pp|e\.g|i\.e|cf|ca|vs|Reg|para|Sec|ss)$/;

/** First sentence of a plain-text rationale; ignores full stops inside abbreviations and [[citation]] tokens. */
export function firstSentence(s: string): string {
  const text = s.trim();
  let depth = 0;
  for (let i = 0; i < text.length; i++) {
    const c = text[i];
    if (c === "[" && text[i + 1] === "[") depth++;
    if (c === "]" && text[i + 1] === "]") depth = Math.max(0, depth - 1);
    if (depth === 0 && (c === "." || c === "!" || c === "?") && (i === text.length - 1 || /\s/.test(text[i + 1]))) {
      if (c === "." && ABBREV.test(text.slice(Math.max(0, i - 6), i))) continue;
      return text.slice(0, i + 1);
    }
  }
  return text;
}

/** Obligations for the user's role and mandatory first; the rest (recommended, conditional, other role) after. */
const CONDITIONAL = /^\s*(only if|required if|solo se|obbligatoria se)/i;
export const isConditional = (o: Obligation) =>
  CONDITIONAL.test(o.summary.en ?? "") || CONDITIONAL.test(o.summary.it ?? "");

export function splitObligations(obligations: Obligation[], role: Role): { core: Obligation[]; extra: Obligation[] } {
  const mine = (o: Obligation) => o.role === "both" || role === "both" || role === "unknown" || role === "other" || o.role === role;
  const core = obligations.filter((o) => o.priority === "must" && mine(o) && !isConditional(o));
  const extra = obligations.filter((o) => !core.includes(o));
  return { core, extra };
}
