"use client";

import { useSearchParams } from "next/navigation";
import { useCallback, useEffect, useRef, useState } from "react";
import { PencilLine, Plus } from "lucide-react";
import { DogScene } from "@/components/pixel/Pixel";
import { Documents } from "@/components/result/Documents";
import { MustDo } from "@/components/result/MustDo";
import { Reasoning } from "@/components/result/Reasoning";
import { Verdict } from "@/components/result/Verdict";
import { WhatIfList } from "@/components/result/WhatIfList";
import { useMeta } from "@/hooks/useMeta";
import { useT } from "@/i18n";
import { ApiError, assess, getExamples } from "@/lib/api";
import type { Answer, Assessment, ExampleItem, FactSheet, Question, Stage, WhatIf } from "@/lib/types";
import { Composer, MIN_CHARS } from "./Composer";
import { InlineQuestions } from "./InlineQuestions";
import { Progress } from "./Progress";

type Phase = "idle" | "running" | "clarify" | "result" | "error";
type FlowError = { code: "network" | "llm_unavailable" | "invalid_input" | "internal"; message?: string };

interface Session {
  description: string;
  sessionId: string | null;
  facts: FactSheet | null;
  answers: Answer[];
  round: number;
  asked: string[];
}

/** Matches the backend's MAX_ROUNDS: a request at this round goes straight to the answer. */
const MAX_ROUNDS = 2;
const EMPTY: Session = { description: "", sessionId: null, facts: null, answers: [], round: 0, asked: [] };
const norm = (s: string) => s.replace(/\[\[[^\]]*\]\]/g, "").replace(/\s+/g, " ").trim();
const saveKey = (id: string) => `aiact.assessment.${id}`;

/** The two mascots, side by side, saying hello. */
function Mascots() {
  const { t } = useT();
  return (
    <div className="relative flex items-end gap-2.5 justify-self-start sm:justify-self-end" data-testid="mascots">
      <span className="pixel-label absolute -top-3 left-[72px] z-10 rounded-full border-2 border-[#111] bg-white px-2.5 py-1 text-[#111] sm:left-[92px]">{t("hero.woof")}</span>
      <div className="px-block overflow-hidden rounded-[1.4rem] px-1.5 pt-3" style={{ "--block": "var(--block-limited)", "--grid": "4px" } as React.CSSProperties}>
        <DogScene scene="hello_schnauzer" label={t("scene.schnauzer")} className="w-[112px] sm:w-[144px]" />
      </div>
      <div className="px-block overflow-hidden rounded-[1.4rem] px-1.5 pt-3" style={{ "--block": "var(--block-prohibited)", "--grid": "4px" } as React.CSSProperties}>
        <DogScene scene="hello_doberman" label={t("scene.doberman")} className="w-[112px] sm:w-[144px]" />
      </div>
      <p className="sr-only">{t("hero.mascots")}</p>
    </div>
  );
}

/** The whole product on one screen: describe → (a few inline questions) → verdict. */
export function Checker() {
  const { t, lang, ready } = useT();
  const { lawAsOf } = useMeta();
  const params = useSearchParams();
  const [phase, setPhase] = useState<Phase>("idle");
  const [text, setText] = useState("");
  const [session, setSession] = useState<Session>(EMPTY);
  const [stages, setStages] = useState<Stage[]>([]);
  const [questions, setQuestions] = useState<Question[]>([]);
  const [streamed, setStreamed] = useState("");
  const [streaming, setStreaming] = useState(false);
  const [assessment, setAssessment] = useState<Assessment | null>(null);
  const [error, setError] = useState<FlowError | null>(null);
  const [examples, setExamples] = useState<ExampleItem[]>([]);
  const [editing, setEditing] = useState(false);
  const [notFound, setNotFound] = useState(false);
  const [regenerated, setRegenerated] = useState(false);
  const abortRef = useRef<AbortController | null>(null);
  const streamedRef = useRef("");
  const bootedRef = useRef(false);
  const resultRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    let alive = true;
    getExamples(lang).then((r) => alive && setExamples(r)).catch(() => undefined);
    return () => { alive = false; };
  }, [lang]);

  const run = useCallback(async (s: Session) => {
    abortRef.current?.abort();
    const ctl = new AbortController();
    abortRef.current = ctl;
    setSession(s);
    setText(s.description);
    setPhase("running");
    setEditing(false);
    setStages([]);
    setQuestions([]);
    setAssessment(null);
    setStreamed("");
    setStreaming(false);
    streamedRef.current = "";
    setRegenerated(false);
    setError(null);
    setNotFound(false);
    let next = s;
    const save = (a: Assessment) => { try { window.localStorage.setItem(saveKey(a.id), JSON.stringify(a)); } catch { /* storage unavailable */ } };
    try {
      for await (const ev of assess({
        description: s.description, language: lang, session_id: s.sessionId, facts: s.facts, answers: s.answers, round: s.round, asked: s.asked,
      }, ctl.signal)) {
        switch (ev.type) {
          case "stage": setStages((p) => (p[p.length - 1] === ev.stage ? p : [...p, ev.stage])); break;
          case "facts": next = { ...next, facts: ev.facts }; break;
          case "questions":
            next = { ...next, facts: ev.facts, sessionId: ev.session_id, round: ev.round, asked: ev.asked ?? next.asked };
            setSession(next);
            setQuestions(ev.questions);
            break;
          case "verdict":
            // The rules have decided: show the answer now, the narrative streams in behind it.
            setAssessment(ev.assessment);
            setStreaming(true);
            setPhase("result");
            break;
          case "token":
            if (ev.section === "reasoning") { streamedRef.current += ev.text; setStreamed((p) => p + ev.text); }
            break;
          case "result":
            setAssessment(ev.assessment);
            setStreaming(false);
            setPhase("result");
            // Server may substitute a fallback after a streaming error; compare ignoring citation tokens/whitespace.
            setRegenerated(streamedRef.current.trim() !== "" && norm(streamedRef.current) !== norm(ev.assessment.reasoning_md));
            save(ev.assessment);
            break;
          case "error":
            setError({ code: ev.code, message: ev.message[lang] ?? ev.message.en });
            setStreaming(false);
            setPhase("error");
            return;
          case "done":
            setStreaming(false);
            setPhase(ev.status === "needs_clarification" ? "clarify" : "result");
            return;
        }
      }
      setStreaming(false);
      setPhase((p) => (p === "running" ? "error" : p));
      setError((e) => e ?? { code: "network" });
    } catch (e) {
      if (e instanceof DOMException && e.name === "AbortError") return;
      setStreaming(false);
      setError({ code: e instanceof ApiError ? "internal" : "network" });
      setPhase("error");
    }
  }, [lang]);

  // Boot from the URL: ?id= (saved result), ?example= (run an example), ?q= (prefilled text).
  useEffect(() => {
    if (!ready || bootedRef.current) return;
    bootedRef.current = true;
    const id = params.get("id");
    const example = params.get("example");
    const q = params.get("q");
    if (id) {
      try {
        const raw = window.localStorage.getItem(saveKey(id));
        if (raw) {
          const a = JSON.parse(raw) as Assessment;
          /* eslint-disable react-hooks/set-state-in-effect */
          setAssessment(a);
          setText(a.description);
          setSession({ ...EMPTY, description: a.description, facts: a.facts });
          setPhase("result");
          /* eslint-enable react-hooks/set-state-in-effect */
          return;
        }
      } catch { /* fall through */ }
      setNotFound(true);
    }
    if (example) {
      getExamples(lang).then((list) => {
        const ex = list.find((e) => e.id === example);
        const body = ex ? (ex.text ?? ex.description) : "";
        if (ex && body.trim().length >= MIN_CHARS) void run({ ...EMPTY, description: body });
        else setText(body);
      }).catch(() => { setError({ code: "network" }); setPhase("error"); });
    } else if (q) {
      if (q.trim().length >= MIN_CHARS) void run({ ...EMPTY, description: q.trim() });
      else setText(q);
    }
  }, [params, lang, run, ready]);

  useEffect(() => () => abortRef.current?.abort(), []);

  // Bring the verdict into view when it first appears.
  const verdictId = assessment?.id;
  useEffect(() => {
    if (verdictId && phase === "result") resultRef.current?.scrollIntoView({ behavior: "smooth", block: "start" });
  }, [verdictId, phase]);

  const cancel = () => {
    abortRef.current?.abort();
    setStreaming(false);
    setPhase("idle");
  };
  const submitAnswers = (answers: Answer[]) => {
    const merged = [...session.answers.filter((a) => !answers.some((n) => n.fact_path === a.fact_path)), ...answers];
    void run({ ...session, answers: merged });
  };
  const applyWhatIf = (w: WhatIf) => {
    if (!assessment) return;
    window.scrollTo({ top: 0, behavior: "smooth" });
    void run({ ...EMPTY, description: assessment.description, facts: assessment.facts, answers: [{ fact_path: w.fact_path, value: w.value }], round: MAX_ROUNDS });
  };
  const newCheck = () => {
    abortRef.current?.abort();
    setAssessment(null);
    setText("");
    setPhase("idle");
    setEditing(false);
    window.history.replaceState(null, "", `/?lang=${lang}`);
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  const showResult = !!assessment && (phase === "result");
  const compact = showResult && !editing;
  const busy = phase === "running";

  return (
    <div className="space-y-3 pb-8 pt-4 sm:pt-8">
      {!showResult && (
        <header className="grid items-end gap-5 px-1 pb-4 sm:grid-cols-[1fr_auto] sm:gap-8 sm:pb-6">
          <div className="min-w-0">
            <p className="pixel-label">{t("hero.eyebrow")}</p>
            <h1 className="display mt-3 max-w-3xl text-balance text-[44px] sm:text-[68px] lg:text-[76px]">{t("hero.title")}</h1>
            <p className="mt-4 max-w-2xl text-[16px] font-medium leading-snug sm:text-[17px]">{t("hero.lede")}</p>
          </div>
          <Mascots />
        </header>
      )}
      {showResult && <h1 className="sr-only">{t("hero.title")}</h1>}

      {notFound && !busy && (
        <div data-testid="not-found" role="status" className="panel flex flex-wrap items-center justify-between gap-3 p-5">
          <div>
            <p className="text-[16px] font-extrabold tracking-tight">{t("assess.notFound.title")}</p>
            <p className="text-[14px] text-muted-foreground">{t("assess.notFound.text")}</p>
          </div>
          <button type="button" onClick={() => { setNotFound(false); window.history.replaceState(null, "", `/?lang=${lang}`); }}
            className="pill pill-secondary h-10 px-4 text-[13.5px]">{t("assess.notFound.cta")}</button>
        </div>
      )}

      {compact ? (
        <div className="panel no-print flex flex-col gap-3 p-4 sm:flex-row sm:items-center sm:p-5" data-testid="input-summary">
          <div className="min-w-0 flex-1">
            <p className="pixel-label text-muted-foreground">{t("input.yours")}</p>
            <p className="mt-1 line-clamp-2 text-[14.5px] font-medium">{assessment.description}</p>
          </div>
          <div className="grid shrink-0 grid-cols-2 gap-2 sm:flex">
            <button type="button" onClick={() => { setText(assessment.description); setEditing(true); }}
              className="pill pill-secondary h-11 px-4 text-[14px]">
              <PencilLine className="size-4" aria-hidden /> {t("input.edit")}
            </button>
            <button type="button" onClick={newCheck} data-testid="new-check"
              className="pill pill-primary h-11 px-4 text-[14px]">
              <Plus className="size-4" aria-hidden /> {t("input.new")}
            </button>
          </div>
        </div>
      ) : (
        <Composer
          text={text}
          onText={setText}
          busy={busy}
          examples={examples}
          onSubmit={(d) => void run({ ...EMPTY, description: d })}
          onExample={(ex) => void run({ ...EMPTY, description: ex.text ?? ex.description })}
        >
          {busy && <Progress seen={stages} onCancel={cancel} />}
          {phase === "clarify" && questions.length > 0 && <InlineQuestions key={session.round} questions={questions} onSubmit={submitAnswers} />}
          {phase === "error" && error && (
            <div role="alert" data-testid="error-card"
              className="px-block fade-up mx-2 mb-2 flex flex-col gap-2 overflow-hidden rounded-[1.4rem] px-5 pt-5 sm:mx-2.5 sm:mb-2.5 sm:flex-row sm:items-end sm:gap-6 sm:px-7"
              style={{ "--block": "var(--block-error)", "--grid": "5px" } as React.CSSProperties}>
              <div className="min-w-0 flex-1 pb-1 sm:pb-6">
                <p className="pixel-label">{t("error.eyebrow")}</p>
                <p className="display mt-2 text-[34px] sm:text-[44px]">{t("error.title")}</p>
                <p className="mt-2 max-w-md text-[15px] font-medium leading-snug">{error.message || t(`error.${error.code}` as const)}</p>
                <button type="button" onClick={() => void run(session)} className="pill pill-primary mt-4 h-12 w-full px-6 text-[15px] sm:w-auto">{t("error.retry")}</button>
              </div>
              <DogScene scene="error" label={t("scene.error")} className="mx-auto w-[150px] shrink-0 sm:mx-0 sm:w-[176px]" />
            </div>
          )}
        </Composer>
      )}

      {showResult && assessment && (
        <div ref={resultRef} className="print-expand scroll-mt-20 space-y-3" data-testid="result-view">
          <Verdict assessment={assessment} lawAsOf={assessment.law_as_of || lawAsOf} />
          <MustDo obligations={assessment.obligations} role={assessment.classification.role} />
          <Documents assessmentId={assessment.id} items={assessment.checklist} />
          <WhatIfList assessment={assessment} onApply={applyWhatIf} />
          <Reasoning
            markdown={streaming ? streamed : assessment.reasoning_md}
            streaming={streaming}
            note={regenerated ? t("reasoning.regenerated") : undefined}
            metrics={streaming ? undefined : `${t("result.metrics", { model: `${assessment.model.provider} / ${assessment.model.model}`, secs: (assessment.metrics.latency_ms / 1000).toFixed(1) })}${assessment.metrics.cost_usd > 0 ? ` · ${t("result.metrics.cost", { cost: assessment.metrics.cost_usd.toFixed(3) })}` : ""}`}
          />
          <p className="px-1 text-[11.5px] leading-relaxed text-muted-foreground" data-testid="disclaimer">{assessment.disclaimer ? (assessment.disclaimer[lang] ?? assessment.disclaimer.en) : null}</p>
        </div>
      )}
    </div>
  );
}
