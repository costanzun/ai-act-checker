"use client";

import { useSearchParams } from "next/navigation";
import { useCallback, useEffect, useRef, useState } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { useT } from "@/i18n";
import { ApiError, assess, getExamples } from "@/lib/api";
import type { Answer, Assessment, FactSheet, Question, Stage } from "@/lib/types";
import { DescribeForm, MIN_CHARS } from "./DescribeForm";
import { ErrorCard, type FlowError } from "./ErrorCard";
import { MAX_ROUNDS, QuestionForm } from "./QuestionForm";
import { ReasoningPanel } from "./ReasoningPanel";
import { ResultSkeleton } from "./ResultSkeleton";
import { ResultView } from "./ResultView";
import { StageTimeline } from "./StageTimeline";
import { Stepper, type StepId } from "./Stepper";

type Phase = "describe" | "running" | "clarify" | "result" | "error";

interface Session {
  description: string;
  sessionId: string | null;
  facts: FactSheet | null;
  answers: Answer[];
  round: number;
}

const EMPTY: Session = { description: "", sessionId: null, facts: null, answers: [], round: 0 };
const saveKey = (id: string) => `aiact.assessment.${id}`;

export function AssessFlow() {
  const { t, lang } = useT();
  const params = useSearchParams();
  const [phase, setPhase] = useState<Phase>("describe");
  const [session, setSession] = useState<Session>(EMPTY);
  const [stages, setStages] = useState<Stage[]>([]);
  const [questions, setQuestions] = useState<Question[]>([]);
  const [streamed, setStreamed] = useState("");
  const [assessment, setAssessment] = useState<Assessment | null>(null);
  const [error, setError] = useState<FlowError | null>(null);
  const abortRef = useRef<AbortController | null>(null);
  const bootedRef = useRef(false);
  const [notFound, setNotFound] = useState(false);

  const run = useCallback(async (s: Session) => {
    abortRef.current?.abort();
    const ctl = new AbortController();
    abortRef.current = ctl;
    setSession(s);
    setPhase("running");
    setStages([]);
    setStreamed("");
    setError(null);
    let next = s;
    try {
      for await (const ev of assess({
        description: s.description, language: lang, session_id: s.sessionId, facts: s.facts, answers: s.answers, round: s.round,
      }, ctl.signal)) {
        switch (ev.type) {
          case "stage": setStages((p) => (p[p.length - 1] === ev.stage ? p : [...p, ev.stage])); break;
          case "facts": next = { ...next, facts: ev.facts }; break;
          case "questions":
            next = { ...next, facts: ev.facts, sessionId: ev.session_id, round: ev.round };
            setSession(next);
            setQuestions(ev.questions);
            break;
          case "token": if (ev.section === "reasoning") setStreamed((p) => p + ev.text); break;
          case "result":
            setAssessment(ev.assessment);
            try { window.localStorage.setItem(saveKey(ev.assessment.id), JSON.stringify(ev.assessment)); } catch { /* ignore */ }
            break;
          case "error": setError({ code: ev.code, message: ev.message[lang] ?? ev.message.en }); setPhase("error"); return;
          case "done": setPhase(ev.status === "needs_clarification" ? "clarify" : "result"); return;
        }
      }
      // stream ended without `done`
      setPhase((p) => (p === "running" ? "error" : p));
      setError((e) => e ?? { code: "network" });
    } catch (e) {
      if (e instanceof DOMException && e.name === "AbortError") return;
      setError({ code: e instanceof ApiError ? "internal" : "network" });
      setPhase("error");
    }
  }, [lang]);

  // Boot from URL: ?id= (saved result), ?example= (run an example), ?q= (text from landing)
  useEffect(() => {
    if (bootedRef.current) return;
    bootedRef.current = true;
    const id = params.get("id");
    const example = params.get("example");
    const q = params.get("q");
    if (id) {
      try {
        const raw = window.localStorage.getItem(saveKey(id));
        if (raw) {
          const a = JSON.parse(raw) as Assessment;
          // eslint-disable-next-line react-hooks/set-state-in-effect
          setAssessment(a);
          setSession({ ...EMPTY, description: a.description });
          setPhase("result");
          return;
        }
      } catch { /* fall through */ }
      setNotFound(true);
    }
    if (example) {
      getExamples(lang).then((list) => {
        const ex = list.find((e) => e.id === example);
        const text = ex ? (ex.text ?? ex.description) : "";
        if (ex && text.trim().length >= MIN_CHARS) void run({ ...EMPTY, description: text });
        else setSession({ ...EMPTY, description: text });
      }).catch(() => { setError({ code: "network" }); setPhase("error"); });
    } else if (q) {
      if (q.trim().length >= MIN_CHARS) void run({ ...EMPTY, description: q.trim() });
      else setSession({ ...EMPTY, description: q });
    }
  }, [params, lang, run]);

  useEffect(() => () => abortRef.current?.abort(), []);

  const submitAnswers = (answers: Answer[]) => {
    const merged = [...session.answers.filter((a) => !answers.some((n) => n.fact_path === a.fact_path)), ...answers];
    void run({ ...session, answers: merged });
  };

  const restart = (keepText: boolean) => {
    abortRef.current?.abort();
    setSession({ ...EMPTY, description: keepText ? session.description : "" });
    setAssessment(null);
    setQuestions([]);
    setStreamed("");
    setPhase("describe");
  };

  const step: StepId = phase === "result" ? "result" : phase === "clarify" ? "clarify"
    : phase === "running" ? (session.answers.length || session.round > 0 ? "clarify" : "describe") : phase === "error" ? (session.round > 0 ? "clarify" : "describe") : "describe";
  const resultCanAsk = !!assessment && assessment.classification.unresolved.length > 0 && session.round < MAX_ROUNDS;

  return (
    <div className="mx-auto max-w-3xl py-8 sm:py-12">
      <h1 className="sr-only">{t("assess.title")}</h1>
      <Stepper current={step} />
      <div className="rule mt-6 pt-8">
        {phase === "describe" && (
          <>
            {notFound ? (
              <Card data-testid="not-found" className="mb-8">
                <CardContent className="space-y-3">
                  <p className="font-heading text-xl font-medium">{t("assess.notFound.title")}</p>
                  <p className="text-sm text-muted-foreground">{t("assess.notFound.text")}</p>
                  <Button onClick={() => { setNotFound(false); window.history.replaceState(null, "", `/assess?lang=${lang}`); }}>{t("assess.notFound.cta")}</Button>
                </CardContent>
              </Card>
            ) : (
              <DescribeForm key={session.description} initial={session.description} onSubmit={(d) => void run({ ...EMPTY, description: d })} />
            )}
          </>
        )}

        {phase === "running" && (
          <div className="space-y-10">
            <Card><CardContent><StageTimeline seen={stages} /></CardContent></Card>
            {streamed ? <ReasoningPanel markdown={streamed} streaming /> : null}
            <ResultSkeleton withReasoning={!streamed} />
          </div>
        )}

        {phase === "clarify" && (
          <div className="space-y-6">
            <p className="rounded-md border border-border bg-card p-3 text-sm text-muted-foreground">{session.description}</p>
            <QuestionForm key={session.round} questions={questions} round={session.round} onSubmit={submitAnswers} />
          </div>
        )}

        {phase === "error" && error && (
          <ErrorCard error={error} onRetry={() => void run(session)} onEdit={() => restart(true)} />
        )}

        {phase === "result" && assessment && (
          <div className="space-y-6">
            <div className="no-print flex flex-wrap items-center justify-between gap-3">
              <p className="line-clamp-2 max-w-xl text-sm text-muted-foreground">{assessment.description}</p>
              <Button variant="ghost" size="sm" onClick={() => restart(false)}>{t("assess.restart")}</Button>
            </div>
            <ResultView assessment={assessment} canAskAgain={resultCanAsk} onAskAgain={() => restart(true)} />
          </div>
        )}
      </div>
    </div>
  );
}
