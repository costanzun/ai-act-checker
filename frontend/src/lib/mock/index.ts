import type { Assessment, AssessRequest, ExampleItem, Lang, LawResponse, Meta, SseEvent, Stage } from "../types";
import { buildMockAssessment, CV_QUESTIONS, DISCLAIMER, pickScenario, TIMELINE, type Scenario } from "./assessments";
import { mockExamples } from "./examples";
import { mockLaw } from "./provisions";

const sleep = (ms: number, signal?: AbortSignal) =>
  new Promise<void>((resolve, reject) => {
    const id = setTimeout(resolve, ms);
    signal?.addEventListener("abort", () => { clearTimeout(id); reject(new DOMException("Aborted", "AbortError")); }, { once: true });
  });

export const mockMeta: Meta = {
  law_as_of: "2026-07-27",
  checked_at: "2026-11-03",
  celex: "02024R1689-20260727",
  amending_acts: [{ celex: "32026R1744", marker: "M1", short_title: "Regulation (EU) 2026/1744 (Digital Omnibus on AI)", oj_date: "2026-07-24", in_force: "2026-07-27" }],
  provider: "mock",
  model: "fixture-v1",
  timeline: TIMELINE,
  disclaimer: DISCLAIMER,
  languages: ["en", "it"],
};

export async function mockGetMeta(): Promise<Meta> { await sleep(120); return mockMeta; }
export async function mockGetExamples(lang: Lang): Promise<ExampleItem[]> { await sleep(150); return mockExamples(lang); }
export async function mockGetLaw(id: string, lang: Lang): Promise<LawResponse> {
  await sleep(180);
  const r = mockLaw(id, lang);
  if (!r) throw new Error(`404 ${id}`);
  return r;
}

const STAGES: { stage: Stage; en: string; it: string }[] = [
  { stage: "extracting", en: "Reading your description", it: "Lettura della descrizione" },
  { stage: "retrieving", en: "Finding relevant provisions", it: "Ricerca delle disposizioni pertinenti" },
  { stage: "classifying", en: "Applying the rules", it: "Applicazione delle regole" },
  { stage: "drafting", en: "Writing the reasoning", it: "Stesura della motivazione" },
];

function toAnswerMap(req: AssessRequest): Record<string, unknown> {
  return Object.fromEntries((req.answers ?? []).map((a) => [a.fact_path, a.value]));
}

/** Simulates the SSE stream of POST /api/assess with realistic delays. */
export async function* mockAssess(req: AssessRequest, signal?: AbortSignal): AsyncGenerator<SseEvent> {
  const scenario: Scenario = pickScenario(req.description);
  const needsQuestions = scenario === "cv" && req.round === 0;

  const stages = needsQuestions ? STAGES.slice(0, 3) : STAGES;
  for (const s of stages) {
    yield { type: "stage", stage: s.stage, message: { en: s.en, it: s.it } };
    await sleep(s.stage === "drafting" ? 250 : 550, signal);
    if (s.stage === "extracting") yield { type: "facts", facts: { sector: scenario === "cv" ? "employment" : null, role: null } };
  }

  if (needsQuestions) {
    yield { type: "questions", questions: CV_QUESTIONS, facts: { sector: "employment", role: null, decision_impact: null }, round: 1, session_id: "mock-session-1" };
    yield { type: "done", status: "needs_clarification" };
    return;
  }

  const assessment: Assessment = buildMockAssessment(scenario, req.language, req.description, toAnswerMap(req));
  // Stream the reasoning word by word.
  const words = assessment.reasoning_md.split(/(\s+)/);
  let buf = "";
  for (const w of words) {
    buf += w;
    if (/\s/.test(w) && buf.length > 14) {
      yield { type: "token", section: "reasoning", text: buf };
      buf = "";
      await sleep(22, signal);
    }
  }
  if (buf) yield { type: "token", section: "reasoning", text: buf };
  yield { type: "stage", stage: "finalising", message: { en: "Preparing your result", it: "Preparazione del risultato" } };
  await sleep(300, signal);
  yield { type: "result", assessment };
  yield { type: "done", status: "complete" };
}

export function mockMarkdown(a: Assessment): string {
  const lang = a.language;
  const l = (x: Record<string, string>) => x[lang] ?? x.en;
  const lines = [
    `# EU AI Act assessment`, "",
    `**Tier:** ${a.classification.tier} (${a.classification.confidence} confidence)`,
    `**Law as of:** ${a.law_as_of} · checked ${a.checked_at}`, "",
    `## Description`, a.description, "",
    `## Reasoning`, a.reasoning_md, "",
    `## Obligations`, ...a.obligations.map((o) => `- **${l(o.title)}**: ${l(o.summary)}`), "",
    `## Checklist`, ...a.checklist.map((c) => `- [ ] ${l(c.title)}`), "",
    `> ${l(a.disclaimer)}`, "",
  ];
  return lines.join("\n");
}
