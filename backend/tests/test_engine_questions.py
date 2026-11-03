"""Tests for the sensitivity-analysis question selector."""

from __future__ import annotations

from app.engine import FactSheet, classify, next_questions
from app.engine.questions import REGISTRY
from tests.test_engine_rules import sheet


def paths(qs) -> list[str]:
    return [q.fact_path for q in qs]


def test_unknown_role_is_asked_for_high_risk():
    f = sheet(role=None, annex_iii_area="4a_recruitment_selection", art63__profiling_of_natural_persons=True)
    qs = next_questions(f)
    assert "role" in paths(qs)
    role_q = next(q for q in qs if q.fact_path == "role")
    assert {o["value"] for o in role_q.options} == {"provider", "deployer", "both", "other"}
    assert all(set(o["label"]) == {"en", "it"} for o in role_q.options)


def test_role_not_asked_for_minimal_risk():
    assert "role" not in paths(next_questions(sheet(role=None)))


def test_fully_specified_sheet_yields_no_questions():
    assert next_questions(sheet()) == []
    f = sheet(annex_iii_area="4a_recruitment_selection", decision_impact="supports_human_decision",
              art63__narrow_procedural_task=True, art63__improves_prior_human_activity=False,
              art63__detects_patterns_without_replacing_assessment=False, art63__preparatory_task_only=False,
              art63__profiling_of_natural_persons=False)
    assert next_questions(f) == []
    assert classify(f).confidence == "high"


def test_impact_ordering_and_cap():
    qs = next_questions(FactSheet(), max_questions=10)
    assert 0 < len(qs) <= 3
    impacts = [q.impact for q in qs]
    assert impacts == sorted(impacts, reverse=True)
    assert all(q.impact > 0 for q in qs)
    # the Annex III use case is the most outcome-changing unknown on an empty sheet
    assert qs[0].fact_path == "annex_iii_area"


def test_asked_paths_are_skipped():
    f = FactSheet()
    first = next_questions(f)
    second = next_questions(f, asked={q.fact_path for q in first})
    assert not set(paths(first)) & set(paths(second))
    third = next_questions(f, asked={q.id for q in first})  # ids are also accepted
    assert paths(third) == paths(second)


def test_derogation_questions_for_annex_iii():
    f = sheet(annex_iii_area="4a_recruitment_selection", decision_impact=None)
    ps = paths(next_questions(f))
    assert "art63.profiling_of_natural_persons" in ps
    assert "decision_impact" in ps


def test_annex_i_chain_question_detected_through_completion():
    # safety_component alone cannot flip the tier while third-party assessment is unknown;
    # the selector must still find it relevant.
    f = sheet(annex_i_product="medical_devices")
    ps = paths(next_questions(f))
    assert "safety_component" in ps


def test_irrelevant_facts_not_asked():
    # a chatbot whose disclosure status is known: emotion/medical questions are gated off
    f = sheet(transparency__interacts_with_natural_persons=True, transparency__obvious_to_users_it_is_ai=False)
    assert next_questions(f) == []


def test_exception_question_for_emotion_recognition_at_work():
    f = sheet(biometric__emotion_recognition=True, context_workplace_or_education=True)
    assert "biometric.medical_or_safety_purpose" in paths(next_questions(f))


def test_questions_are_bilingual_and_typed():
    for q in next_questions(FactSheet()) + next_questions(sheet(role=None, social_scoring=True)):
        assert set(q.text) == {"en", "it"} and set(q.why) == {"en", "it"}
        assert q.type in ("single", "boolean")
        assert q.id == f"q-{q.fact_path}"


def test_registry_paths_exist_in_factsheet():
    f = FactSheet()
    for e in REGISTRY:
        f.with_answer(e.path, e.options[0]["value"])  # raises if the path or value is invalid
