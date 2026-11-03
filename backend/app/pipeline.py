"""Assessment pipeline: description → facts → (questions | classification + cited narrative).

Flow (see PLAN.md §3):
1. extract facts with the LLM (skipped when the client sends prior facts);
2. apply the user's answers deterministically;
3. classify with the rule engine; ask questions chosen by sensitivity analysis
   when a decisive fact is unknown (max rounds);
4. retrieve related provisions and the texts of the cited ones;
5. stream the narrative from the LLM, constrained to an allow-list of IDs;
6. assemble obligations, checklist, metrics.

The pipeline yields ``(event_name, payload)`` tuples so the API can forward them
as SSE and the eval runner can consume them directly.
"""

from __future__ import annotations

import logging
import re
import time
from collections.abc import AsyncIterator, Awaitable, Callable
from pathlib import Path
from typing import Any
from uuid import uuid4

from app import engine
from app.corpus.store import CorpusStore
from app.engine.facts import FactSheet
from app.engine.models import Classification, Question
from app.llm import LLMError, LLMProvider, LLMResult, get_provider, parse_json_object
from app.prompts import extract_messages, narrative_messages
from app.schemas import (
    Answer,
    AssessRequest,
    Assessment,
    Metrics,
    ModelInfo,
    QuestionsPayload,
    RelatedProvision,
)

log = logging.getLogger("ai_act.pipeline")

CITE_RE = re.compile(r"\[\[([a-z]+:[A-Za-z0-9.\-]+)\]\]")
MAX_ROUNDS = 2
MAX_QUESTIONS = 3

Event = tuple[str, dict[str, Any]]

STAGES = {
    "extracting": {"en": "Reading your description and extracting the facts", "it": "Lettura della descrizione ed estrazione dei fatti"},
    "classifying": {"en": "Applying the Act's classification rules", "it": "Applicazione delle regole di classificazione"},
    "retrieving": {"en": "Looking up the cited provisions", "it": "Ricerca delle disposizioni citate"},
    "drafting": {"en": "Writing the cited reasoning", "it": "Redazione della motivazione con citazioni"},
    "finalising": {"en": "Assembling obligations and checklist", "it": "Composizione di obblighi e checklist"},
}


class Pipeline:
    def __init__(
        self,
        store: CorpusStore,
        provider: LLMProvider | None = None,
        retriever: Any | None = None,
    ) -> None:
        self.store = store
        self._provider = provider
        self._retriever = retriever

    # ------------------------------------------------------------------ helpers
    def provider_for(self, req: AssessRequest) -> LLMProvider:
        if req.provider or req.model:
            return get_provider(req.provider, req.model)
        if self._provider is None:
            self._provider = get_provider()
        return self._provider

    @property
    def retriever(self) -> Any | None:
        if self._retriever is None:
            try:
                from app.retrieval import get_retriever

                self._retriever = get_retriever()
            except Exception as exc:  # retrieval is optional for the core flow
                log.warning("retriever unavailable: %s", exc)
                self._retriever = False
        return self._retriever or None

    @staticmethod
    def _stage(name: str) -> Event:
        return ("stage", {"stage": name, "message": STAGES[name]})

    @staticmethod
    def _apply_answers(facts: FactSheet, answers: list[Answer]) -> FactSheet:
        for a in answers:
            if a.value in ("", "unknown", "not_sure", None):
                continue
            try:
                facts = facts.with_answer(a.fact_path, a.value)
            except Exception as exc:
                log.warning("ignored answer %s=%r: %s", a.fact_path, a.value, exc)
        return facts

    @staticmethod
    def _add_usage(m: Metrics, r: LLMResult) -> None:
        m.llm_calls += 1
        m.input_tokens += r.input_tokens or 0
        m.output_tokens += r.output_tokens or 0
        m.cost_usd = round(m.cost_usd + (r.cost_usd or 0.0), 6)
        m.cached = m.cached or r.cached

    # ------------------------------------------------------------------- steps
    async def extract_facts(self, description: str, provider: LLMProvider, metrics: Metrics) -> FactSheet:
        messages = extract_messages(description)
        last_err: Exception | None = None
        for attempt in range(2):
            res = await provider.complete(messages, temperature=0.0, max_tokens=1800, json_mode=True)
            self._add_usage(metrics, res)
            try:
                data = parse_json_object(res.text)
                return FactSheet.model_validate(_coerce_nulls(data))
            except Exception as exc:  # JSON or validation problem: retry once with a nudge
                last_err = exc
                log.warning("fact extraction attempt %d failed: %s", attempt + 1, exc)
                messages = messages + [
                    {"role": "assistant", "content": res.text[:4000]},
                    {"role": "user", "content": f"That was not valid for the schema ({str(exc)[:300]}). Return ONLY the corrected JSON object."},
                ]
        raise LLMError(f"could not extract facts: {last_err}")

    def allowed_ids(self, classification: Classification, obligations: list, related: list[RelatedProvision]) -> list[str]:
        ids: list[str] = []
        for f in classification.findings:
            ids += f.citations
        for m in classification.applies_from:
            ids += m.citations
        for o in obligations:
            ids += o.citations
        ids += [r.id for r in related]
        for lst in classification.overlays.values():
            ids += lst
        seen: set[str] = set()
        out: list[str] = []
        for i in ids:
            if i not in seen and self.store.exists(i):
                seen.add(i)
                out.append(i)
        return out

    def sanitize_citations(self, text: str, allowed: set[str], metrics: Metrics) -> str:
        def repl(m: re.Match[str]) -> str:
            pid = m.group(1)
            if pid in allowed:
                return m.group(0)
            metrics.stripped_citations += 1
            return ""

        cleaned = CITE_RE.sub(repl, text)
        return re.sub(r"[ \t]{2,}", " ", cleaned).replace(" .", ".").replace(" ,", ",").strip()

    def related_provisions(self, facts: FactSheet, lang: str, exclude: set[str]) -> list[RelatedProvision]:
        r = self.retriever
        if r is None:
            return []
        try:
            hits = r.related_for_facts(facts.model_dump(), lang=lang, k=8)
        except Exception as exc:
            log.warning("related_for_facts failed: %s", exc)
            return []
        out: list[RelatedProvision] = []
        for h in hits:
            if h["id"] in exclude or not self.store.exists(h["id"]):
                continue
            out.append(
                RelatedProvision(
                    id=h["id"],
                    label=h["label"],
                    why={"en": "Retrieved as relevant to the facts you described", "it": "Individuata come pertinente ai fatti descritti"},
                )
            )
            if len(out) >= 5:
                break
        return out

    # --------------------------------------------------------------------- run
    async def run(self, req: AssessRequest) -> AsyncIterator[Event]:
        t0 = time.perf_counter()
        metrics = Metrics()
        provider = self.provider_for(req)
        lang = req.language
        session_id = req.session_id or str(uuid4())

        # 1. facts
        if req.facts is None:
            yield self._stage("extracting")
            facts = await self.extract_facts(req.description, provider, metrics)
        else:
            facts = req.facts
        facts = self._apply_answers(facts, req.answers)
        yield ("facts", {"facts": facts.model_dump()})

        # 2. classify + questions
        yield self._stage("classifying")
        classification = engine.classify(facts)
        asked = set(req.asked)
        if req.round < MAX_ROUNDS:
            questions: list[Question] = engine.next_questions(facts, max_questions=MAX_QUESTIONS, asked=asked)
            if questions:
                payload = QuestionsPayload(
                    questions=questions,
                    facts=facts,
                    round=req.round + 1,
                    session_id=session_id,
                    asked=sorted(asked | {q.id for q in questions}),
                )
                yield ("questions", payload.model_dump())
                yield ("done", {"status": "needs_clarification"})
                return

        # 3. obligations / checklist / retrieval
        yield self._stage("retrieving")
        obligations = engine.obligations_for(classification, facts)
        checklist = engine.checklist_for(obligations)
        cited = {c for f in classification.findings for c in f.citations}
        related = self.related_provisions(facts, lang, exclude=cited)
        allowed = self.allowed_ids(classification, obligations, related)
        excerpt_ids = [c for f in classification.findings for c in f.citations][:8]
        excerpts = {pid: self.store.full_text(pid, lang) for pid in dict.fromkeys(excerpt_ids) if self.store.exists(pid)}

        # 4. narrative (streamed)
        yield self._stage("drafting")
        messages = narrative_messages(
            description=req.description,
            facts=facts.model_dump(),
            classification=classification.model_dump(),
            excerpts=excerpts,
            allowed_ids=allowed,
            language=lang,
        )
        chunks: list[str] = []
        try:
            async for item in provider.stream(messages, temperature=0.2, max_tokens=900):
                if isinstance(item, str):
                    chunks.append(item)
                    yield ("token", {"section": "reasoning", "text": item})
                else:
                    self._add_usage(metrics, item)
        except LLMError as exc:
            log.error("narrative failed: %s", exc)
            chunks = [_fallback_narrative(classification, lang)]
        reasoning = self.sanitize_citations("".join(chunks), set(allowed), metrics)

        # 5. assemble
        yield self._stage("finalising")
        uncertainties = list(classification.assumptions)
        for path in classification.unresolved:
            uncertainties.append({"en": f"Not stated: {path.replace('_', ' ').replace('.', ' → ')}", "it": f"Non indicato: {path.replace('_', ' ').replace('.', ' → ')}"})
        metrics.latency_ms = int((time.perf_counter() - t0) * 1000)
        assessment = Assessment(
            language=lang,
            model=ModelInfo(provider=provider.name, model=provider.model),
            description=req.description,
            facts=facts,
            classification=classification,
            reasoning_md=reasoning,
            obligations=obligations,
            checklist=checklist,
            related_provisions=related,
            uncertainties=uncertainties,
            metrics=metrics,
        )
        yield ("result", {"assessment": assessment.model_dump()})
        yield ("done", {"status": "complete"})

    # ------------------------------------------------------------- eval helper
    async def assess_blocking(
        self,
        description: str,
        language: str = "en",
        answer_fn: Callable[[Question], Awaitable[Any] | Any] | None = None,
        provider: str | None = None,
        model: str | None = None,
    ) -> tuple[Assessment | None, dict[str, Any]]:
        """Run the full flow, auto-answering questions via ``answer_fn``.

        Returns (assessment or None, trace) where trace records rounds,
        questions asked and the answers given. Used by the eval runner.
        """
        trace: dict[str, Any] = {"rounds": 0, "questions": [], "answers": []}
        req = AssessRequest(description=description, language=language, provider=provider, model=model)  # type: ignore[arg-type]
        facts: FactSheet | None = None
        asked: list[str] = []
        for _ in range(MAX_ROUNDS + 1):
            result: Assessment | None = None
            pending: list[Question] = []
            async for name, payload in self.run(req):
                if name == "questions":
                    pending = [Question.model_validate(q) for q in payload["questions"]]
                    facts = FactSheet.model_validate(payload["facts"])
                    asked = payload["asked"]
                elif name == "result":
                    result = Assessment.model_validate(payload["assessment"])
            if result is not None:
                return result, trace
            if not pending:
                return None, trace
            trace["rounds"] += 1
            answers: list[Answer] = []
            for q in pending:
                trace["questions"].append(q.fact_path)
                value = None
                if answer_fn is not None:
                    value = answer_fn(q)
                    if hasattr(value, "__await__"):
                        value = await value
                trace["answers"].append({"fact_path": q.fact_path, "value": value})
                if value is not None:
                    answers.append(Answer(fact_path=q.fact_path, value=value))
            req = AssessRequest(
                description=description,
                language=language,  # type: ignore[arg-type]
                facts=facts,
                answers=answers,
                asked=asked,
                round=req.round + 1,
                provider=provider,
                model=model,
            )
        return None, trace


def _coerce_nulls(data: dict[str, Any]) -> dict[str, Any]:
    """Small models sometimes write "null"/"unknown" strings; map them to None."""
    def fix(v: Any) -> Any:
        if isinstance(v, dict):
            return {k: fix(x) for k, x in v.items()}
        if isinstance(v, list):
            return [fix(x) for x in v]
        if isinstance(v, str) and v.strip().lower() in {"null", "none", "unknown", "n/a", "not stated"}:
            return None
        return v

    return fix(data)


def _fallback_narrative(c: Classification, lang: str) -> str:
    decisive = next((f for f in c.findings if f.decisive), None)
    if decisive is None:
        return ""
    title = decisive.title.get(lang) or decisive.title.get("en", "")
    rationale = decisive.rationale.get(lang) or decisive.rationale.get("en", "")
    cites = " ".join(f"[[{x}]]" for x in decisive.citations)
    return f"{title}. {rationale} {cites}".strip()


_default: Pipeline | None = None


def get_pipeline(data_dir: Path | None = None) -> Pipeline:
    global _default
    if _default is None:
        root = Path(__file__).resolve().parents[2]
        _default = Pipeline(CorpusStore(data_dir or root / "data" / "corpus"))
    return _default
