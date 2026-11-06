"""'What would change the answer': engine counterfactuals, and the early verdict event."""

from __future__ import annotations

import asyncio
from pathlib import Path

from app.corpus.store import CorpusStore
from app.engine import classify, what_would_change
from app.engine.rules import probe
from app.llm import base, settings
from app.llm.base import LLMProvider, LLMResult
from app.pipeline import MAX_ROUNDS, Pipeline
from app.schemas import AssessRequest
from tests.test_engine_rules import sheet

STORE = CorpusStore(Path(__file__).parent.parent.parent / "data" / "corpus")


def test_items_never_change_the_classification_and_all_move_the_tier():
    f = sheet(annex_iii_area="4a_recruitment_selection", decision_impact="determines_outcome", art63__profiling_of_natural_persons=None)
    before = classify(f)
    items = what_would_change(f, before)
    assert classify(f).model_dump() == before.model_dump()
    assert items, "a high-risk Annex III result has counterfactuals"
    for it in items:
        assert it.tier != before.tier
        assert set(it.question) == {"en", "it"} and set(it.answer) == {"en", "it"}
        if it.actionable:
            assert probe(f, it.fact_path, it.value).tier == it.tier


def test_unresolved_first_and_art63_shown_once():
    f = sheet(annex_iii_area="4a_recruitment_selection", decision_impact="supports_human_decision",
              art63__narrow_procedural_task=None, art63__improves_prior_human_activity=None,
              art63__detects_patterns_without_replacing_assessment=None, art63__preparatory_task_only=None,
              art63__profiling_of_natural_persons=None)
    items = what_would_change(f, classify(f))
    assert items[0].unresolved
    assert items[0].current == {"en": "Not stated", "it": "Non indicato"}
    art63 = [i for i in items if i.fact_path.startswith("art63.") or i.fact_path == "decision_impact"]
    assert len(art63) == 1
    assert len(items) <= 4


def test_annex_i_product_counterfactuals():
    f = sheet(annex_i_product="medical_devices", safety_component=True, annex_i_third_party_assessment=True)
    c = classify(f)
    assert c.tier == "high_risk"
    paths = [i.fact_path for i in what_would_change(f, c)]
    assert "safety_component" in paths and paths[-1] == "annex_i_product"


def test_minimal_risk_gets_transparency_and_generic_annex_iii_item():
    f = sheet()
    c = classify(f)
    assert c.tier == "minimal_risk"
    items = what_would_change(f, c)
    assert any(i.fact_path.startswith("transparency.") and i.tier == "limited_risk" for i in items)
    generic = items[-1]
    assert generic.fact_path == "annex_iii_area" and not generic.actionable and generic.tier == "high_risk"


def test_prohibited_without_alternatives_is_empty_or_valid():
    f = sheet(social_scoring=True)
    c = classify(f)
    assert c.tier == "prohibited"
    for it in what_would_change(f, c):
        assert it.tier != "prohibited"


class _Narrator(LLMProvider):
    name = "fake"
    model = "m1"

    async def _complete(self, messages, *, temperature, max_tokens, json_mode):  # pragma: no cover - not used
        raise AssertionError("facts are supplied; extraction must not run")

    async def _stream(self, messages, *, temperature, max_tokens):
        yield "Annex III applies "
        yield "[[annex:III.4.a]]."
        yield LLMResult("Annex III applies [[annex:III.4.a]].", "m1", "fake", 1, 1, 0.0, 1)


def test_pipeline_sends_verdict_before_the_narrative(tmp_path, monkeypatch):
    monkeypatch.setenv("LLM_CACHE", "0")
    settings.get_settings.cache_clear()
    base._cache = None
    try:
        f = sheet(annex_iii_area="4a_recruitment_selection", decision_impact="determines_outcome",
                  art63__profiling_of_natural_persons=True, role="deployer")
        p = Pipeline(STORE, provider=_Narrator(), retriever=False)
        req = AssessRequest(description="We rank job applicants' CVs for our HR team.", facts=f, round=MAX_ROUNDS)

        async def collect():
            return [e async for e in p.run(req)]

        events = asyncio.run(collect())
    finally:
        base._cache = None
        settings.get_settings.cache_clear()
    names = [n for n, _ in events]
    assert names.index("verdict") < names.index("token") < names.index("result")
    verdict = dict(events)["verdict"]["assessment"]
    result = dict(events)["result"]["assessment"]
    assert verdict["reasoning_md"] == ""
    assert verdict["classification"] == result["classification"]
    assert verdict["what_if"] == result["what_if"] and result["what_if"]
    assert "[[annex:III.4.a]]" in result["reasoning_md"]
