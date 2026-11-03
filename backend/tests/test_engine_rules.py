"""Table-driven tests for app.engine.rules.classify."""

from __future__ import annotations

from typing import Any

import pytest

from app.engine import FactSheet, classify
from app.engine.knowledge.annexes import ANNEX_III


def sheet(**overrides: Any) -> FactSheet:
    """A fully specified 'nothing special' fact sheet, then overrides (dotted keys via __)."""
    data: dict[str, Any] = {
        "is_ai_system": True,
        "role": "provider",
        "in_eu_scope": True,
        "scope_exclusion": "none",
        "annex_iii_area": "none",
        "annex_i_product": "none",
        "decision_impact": "no_decision_about_persons",
        "context_workplace_or_education": False,
        "social_scoring": False,
        "nudify_or_sexual_abuse_material": False,
        "intimate_content_foreseeable_without_safeguards": False,
        "public_body_or_public_service": False,
        "biometric": {k: False for k in (
            "uses_biometric_data", "remote_identification", "real_time", "publicly_accessible_space",
            "categorisation", "infers_sensitive_attributes", "emotion_recognition", "verification_only",
        )},
        "manipulation": {"subliminal_or_deceptive": False, "exploits_vulnerabilities": False,
                         "distorts_behaviour_significant_harm": False},
        "gpai": {"is_gpai_model": False, "provider_of_model": False, "systemic_risk": False,
                 "integrates_third_party_gpai": False, "substantially_modifies_model": False},
        "transparency": {"interacts_with_natural_persons": False, "generates_synthetic_content": False,
                         "deepfake": False, "public_interest_text": False},
        "law_enforcement": {"used_by_or_for_law_enforcement": False, "predictive_policing_profiling_only": False,
                            "untargeted_facial_scraping": False},
    }
    f = FactSheet.model_validate(data)
    for k, v in overrides.items():
        f = f.with_answer(k.replace("__", "."), v)
    return f


def rule_ids(c) -> set[str]:
    return {f.rule_id for f in c.findings}


def cites(c) -> set[str]:
    return {x for f in c.findings for x in f.citations}


# id, overrides, tier, rule id expected, citations expected
PROHIBITION_CASES = [
    ("5.1.a", dict(manipulation__subliminal_or_deceptive=True, manipulation__distorts_behaviour_significant_harm=True),
     "art5.1.a-manipulation", "art:5.1.a"),
    ("5.1.b", dict(manipulation__exploits_vulnerabilities=True, manipulation__distorts_behaviour_significant_harm=True),
     "art5.1.b-exploiting-vulnerabilities", "art:5.1.b"),
    ("5.1.ba", dict(transparency__generates_synthetic_content=True, nudify_or_sexual_abuse_material=True),
     "art5.1.ba-bb-intimate-csam", "art:5.1.ba"),
    ("5.1a.a.ii", dict(transparency__generates_synthetic_content=True, intimate_content_foreseeable_without_safeguards=True),
     "art5.1a.a.ii-foreseeable-without-safeguards", "art:5.1a"),
    ("5.1.c", dict(social_scoring=True), "art5.1.c-social-scoring", "art:5.1.c"),
    ("5.1.d", dict(law_enforcement__predictive_policing_profiling_only=True), "art5.1.d-predictive-policing", "art:5.1.d"),
    ("5.1.e", dict(law_enforcement__untargeted_facial_scraping=True), "art5.1.e-facial-scraping", "art:5.1.e"),
    ("5.1.f", dict(biometric__emotion_recognition=True, context_workplace_or_education=True,
                   biometric__medical_or_safety_purpose=False),
     "art5.1.f-emotion-workplace-education", "art:5.1.f"),
    ("5.1.g", dict(biometric__categorisation=True, biometric__infers_sensitive_attributes=True,
                   biometric__dataset_labelling_or_law_enforcement=False),
     "art5.1.g-biometric-categorisation-sensitive", "art:5.1.g"),
    ("5.1.h", dict(biometric__remote_identification=True, biometric__real_time=True,
                   biometric__publicly_accessible_space=True, law_enforcement__used_by_or_for_law_enforcement=True,
                   law_enforcement__rbi_strictly_necessary_objective=False),
     "art5.1.h-realtime-rbi-law-enforcement", "art:5.1.h"),
]


@pytest.mark.parametrize("cid,overrides,rule,cite", PROHIBITION_CASES, ids=[c[0] for c in PROHIBITION_CASES])
def test_prohibitions(cid, overrides, rule, cite):
    c = classify(sheet(**overrides))
    assert c.tier == "prohibited"
    assert rule in rule_ids(c)
    assert cite in cites(c)
    assert any(f.decisive and f.kind == "prohibition" for f in c.findings)


def test_emotion_recognition_medical_safety_exception_is_high_risk():
    c = classify(sheet(biometric__emotion_recognition=True, context_workplace_or_education=True,
                       biometric__medical_or_safety_purpose=True))
    assert c.tier == "high_risk"
    assert "annex-iii-1c" in rule_ids(c)
    assert c.overlays["transparency_art50"] == ["art:50.3"]


def test_emotion_recognition_exception_unknown_is_conservative():
    c = classify(sheet(biometric__emotion_recognition=True, context_workplace_or_education=True))
    assert c.tier == "prohibited"
    assert "biometric.medical_or_safety_purpose" in c.unresolved
    assert c.confidence == "low"
    assert any("medical" in a["en"] for a in c.assumptions)


def test_emotion_recognition_outside_work_is_high_risk_not_prohibited():
    c = classify(sheet(biometric__emotion_recognition=True))
    assert c.tier == "high_risk"
    assert "art5.1.f-emotion-workplace-education" not in rule_ids(c)


def test_biometric_categorisation_labelling_exception():
    c = classify(sheet(biometric__categorisation=True, biometric__infers_sensitive_attributes=True,
                       biometric__dataset_labelling_or_law_enforcement=True))
    assert c.tier == "high_risk"
    assert "annex-iii-1b" in rule_ids(c)


def test_biometric_categorisation_non_sensitive_is_limited():
    c = classify(sheet(biometric__categorisation=True))  # e.g. by clothing colour
    assert c.tier == "limited_risk"
    assert c.overlays["transparency_art50"] == ["art:50.3"]


def test_realtime_rbi_listed_objective_is_high_risk():
    c = classify(sheet(biometric__remote_identification=True, biometric__real_time=True,
                       biometric__publicly_accessible_space=True, law_enforcement__used_by_or_for_law_enforcement=True,
                       law_enforcement__rbi_strictly_necessary_objective=True))
    assert c.tier == "high_risk"
    assert {"annex-iii-1a", "art5.2-rbi-authorised-objective"} <= rule_ids(c)


def test_foreseeable_intimate_content_not_prohibited_for_deployer():
    c = classify(sheet(role="deployer", transparency__generates_synthetic_content=True,
                       intimate_content_foreseeable_without_safeguards=True))
    assert c.tier == "limited_risk"


def test_new_prohibition_applies_from_dec_2026():
    c = classify(sheet(transparency__generates_synthetic_content=True, nudify_or_sexual_abuse_material=True))
    assert "2026-12-02" in {m.date for m in c.applies_from}


# ---- Annex III, one case per point -------------------------------------------------
ANNEX_III_CASES = [(area, pid) for area, (pid, *_rest) in ANNEX_III.items()]


@pytest.mark.parametrize("area,pid", ANNEX_III_CASES, ids=[a for a, _ in ANNEX_III_CASES])
def test_annex_iii_points_are_high_risk(area, pid):
    c = classify(sheet(annex_iii_area=area, decision_impact="materially_influences",
                       art63__profiling_of_natural_persons=False, art63__narrow_procedural_task=False,
                       art63__improves_prior_human_activity=False,
                       art63__detects_patterns_without_replacing_assessment=False, art63__preparatory_task_only=False))
    assert c.tier == "high_risk"
    assert {"art:6.2", pid} <= cites(c)
    assert c.confidence == "high"
    assert "2027-12-02" in {m.date for m in c.applies_from}


def test_art_6_3_derogation_applies():
    c = classify(sheet(annex_iii_area="4a_recruitment_selection", decision_impact="supports_human_decision",
                       art63__narrow_procedural_task=True, art63__profiling_of_natural_persons=False))
    assert c.tier == "minimal_risk"
    d = [f for f in c.findings if f.rule_id == "art6.3-derogation"]
    assert d and d[0].decisive
    assert {"art:6.3", "art:6.3.a", "art:6.4", "art:49.2"} <= set(d[0].citations)


def test_profiling_defeats_derogation():
    c = classify(sheet(annex_iii_area="4a_recruitment_selection", decision_impact="supports_human_decision",
                       art63__narrow_procedural_task=True, art63__profiling_of_natural_persons=True))
    assert c.tier == "high_risk"
    assert "art6.3-profiling-always-high-risk" in rule_ids(c)
    assert "art6.3-derogation" not in rule_ids(c)


def test_material_influence_defeats_derogation_conservatively():
    c = classify(sheet(annex_iii_area="5b_creditworthiness", decision_impact="materially_influences",
                       art63__preparatory_task_only=True, art63__profiling_of_natural_persons=False))
    assert c.tier == "high_risk"
    assert "art6.3-material-influence" in rule_ids(c)


def test_derogation_unknown_facts_stay_high_risk_with_low_confidence():
    c = classify(sheet(annex_iii_area="3b_education_evaluation", decision_impact=None))
    assert c.tier == "high_risk"
    assert c.confidence == "low"
    assert "art63.profiling_of_natural_persons" in c.unresolved


def test_credit_fraud_detection_exception():
    c = classify(sheet(annex_iii_area="5b_creditworthiness", financial_fraud_detection=True))
    assert c.tier == "minimal_risk"


# ---- Annex I ---------------------------------------------------------------------------
def test_annex_i_medical_device_safety_component():
    c = classify(sheet(annex_i_product="medical_devices", safety_component=True, annex_i_third_party_assessment=True))
    assert c.tier == "high_risk"
    assert {"art:6.1", "annex:I.A.11"} <= cites(c)
    assert "2028-08-02" in {m.date for m in c.applies_from}


def test_annex_i_section_b_machinery_moved_by_omnibus():
    c = classify(sheet(annex_i_product="machinery", safety_component=True, annex_i_third_party_assessment=True,
                       transparency__interacts_with_natural_persons=True,
                       transparency__obvious_to_users_it_is_ai=False))
    assert c.tier == "high_risk"
    assert {"art:2.2", "annex:I.B.21"} <= cites(c)
    assert "transparency_art50" not in c.overlays  # Art. 2(2): only Art. 6(1), 60a, 102-112 apply


def test_annex_i_without_third_party_assessment_not_high_risk():
    c = classify(sheet(annex_i_product="toys", safety_component=True, annex_i_third_party_assessment=False))
    assert c.tier == "minimal_risk"
    assert "art6.1c-no-third-party-assessment" in rule_ids(c)


# ---- Transparency, minimal, out of scope ---------------------------------------------
def test_customer_service_chatbot_is_limited_risk():
    c = classify(sheet(transparency__interacts_with_natural_persons=True, transparency__obvious_to_users_it_is_ai=False,
                       gpai__integrates_third_party_gpai=True, gpai__substantially_modifies_model=False))
    assert c.tier == "limited_risk"
    assert c.overlays == {"transparency_art50": ["art:50.1"]}
    assert "gpai-integrator-not-provider" in rule_ids(c)
    assert c.confidence == "high"


def test_chatbot_obviousness_unknown_lowers_confidence():
    c = classify(sheet(transparency__interacts_with_natural_persons=True))
    assert c.tier == "limited_risk"
    assert "transparency.obvious_to_users_it_is_ai" in c.unresolved
    assert c.confidence == "low"


def test_obvious_ai_interaction_is_minimal():
    c = classify(sheet(transparency__interacts_with_natural_persons=True, transparency__obvious_to_users_it_is_ai=True))
    assert c.tier == "minimal_risk"


def test_deepfake_generator():
    c = classify(sheet(role="both", transparency__generates_synthetic_content=True, transparency__deepfake=True))
    assert c.tier == "limited_risk"
    assert set(c.overlays["transparency_art50"]) == {"art:50.2", "art:50.4"}


def test_public_interest_text_with_editorial_control_is_exempt():
    c = classify(sheet(role="deployer", transparency__generates_synthetic_content=True,
                       transparency__public_interest_text=True, transparency__human_editorial_control=True))
    assert c.overlays["transparency_art50"] == ["art:50.2"]


def test_spam_filter_is_minimal_high_confidence():
    c = classify(sheet(purpose="Spam filter"))
    assert c.tier == "minimal_risk"
    assert c.confidence == "high"
    assert {"art:95", "art:4.1"} <= cites(c)
    assert c.unresolved == []


def test_high_risk_with_unknown_overlay_is_medium_confidence():
    f = sheet(annex_iii_area="4a_recruitment_selection", decision_impact="materially_influences",
              art63__profiling_of_natural_persons=True)
    f = f.with_answer("transparency.interacts_with_natural_persons", None)
    c = classify(f)
    assert c.tier == "high_risk"
    assert c.confidence == "medium"


@pytest.mark.parametrize(
    "excl,rule,cite",
    [
        ("scientific_research_only", "art2.6-scientific-research", "art:2.6"),
        ("military_defence_national_security", "art2.3-military", "art:2.3"),
        ("pre_market_research_testing", "art2.8-pre-market-rnd", "art:2.8"),
        ("personal_non_professional", "art2.10-personal-use", "art:2.10"),
        ("third_country_public_authority_cooperation", "art2.4-third-country-cooperation", "art:2.4"),
    ],
)
def test_scope_exclusions(excl, rule, cite):
    role = "deployer" if excl == "personal_non_professional" else "provider"
    c = classify(sheet(scope_exclusion=excl, role=role, social_scoring=True))  # exclusion precedes Art. 5
    assert c.tier == "out_of_scope"
    assert rule in rule_ids(c)
    assert cite in cites(c)


def test_personal_use_does_not_exclude_providers():
    c = classify(sheet(scope_exclusion="personal_non_professional", role="provider"))
    assert c.tier == "minimal_risk"


def test_rule_based_payroll_is_not_ai_system():
    c = classify(sheet(is_ai_system=False, purpose="Payroll calculation with fixed rules"))
    assert c.tier == "out_of_scope"
    assert "art3.1-not-ai-system" in rule_ids(c)
    assert {"art:3.1", "rec:12"} <= cites(c)


def test_no_eu_nexus():
    c = classify(sheet(in_eu_scope=False))
    assert c.tier == "out_of_scope"


def test_open_source_minimal_system_excluded():
    c = classify(sheet(free_open_source_licence=True))
    assert c.tier == "out_of_scope"
    assert "art:2.12" in cites(c)


def test_open_source_high_risk_not_excluded():
    c = classify(sheet(free_open_source_licence=True, annex_iii_area="4a_recruitment_selection",
                       art63__profiling_of_natural_persons=True))
    assert c.tier == "high_risk"


# ---- GPAI ---------------------------------------------------------------------------
def test_gpai_model_provider():
    c = classify(sheet(is_ai_system=False, gpai__is_gpai_model=True, gpai__provider_of_model=True))
    assert c.tier == "minimal_risk"  # the model itself is not an AI system; GPAI duties are an overlay
    assert c.overlays["gpai"] == ["art:53", "art:54"]


def test_gpai_systemic_risk():
    c = classify(sheet(gpai__is_gpai_model=True, gpai__provider_of_model=True, gpai__systemic_risk=True))
    assert "art:55" in c.overlays["gpai"]
    assert {"art:51", "art:55"} <= cites(c)


def test_gpai_integrator_is_not_gpai_provider():
    c = classify(sheet(gpai__integrates_third_party_gpai=True, gpai__substantially_modifies_model=False))
    assert "gpai" not in c.overlays
    assert {"art:3.68", "art:25.1"} <= cites(c)


def test_gpai_integrator_substantial_modification():
    c = classify(sheet(gpai__integrates_third_party_gpai=True, gpai__substantially_modifies_model=True))
    assert c.overlays.get("gpai") == ["art:53"]


def test_overlays_are_additive_on_high_risk():
    c = classify(sheet(annex_iii_area="4a_recruitment_selection", art63__profiling_of_natural_persons=True,
                       transparency__interacts_with_natural_persons=True,
                       transparency__obvious_to_users_it_is_ai=False))
    assert c.tier == "high_risk"
    assert c.overlays["transparency_art50"] == ["art:50.1"]


def test_unknown_role_recorded():
    c = classify(sheet(role=None, annex_iii_area="4a_recruitment_selection", art63__profiling_of_natural_persons=True))
    assert c.role == "unknown"
    assert "role" in c.unresolved
    assert any("role" in a["en"].lower() for a in c.assumptions)


def test_empty_sheet_is_low_confidence_minimal():
    c = classify(FactSheet())
    assert c.tier == "minimal_risk"
    assert c.confidence == "low"
    assert "is_ai_system" in c.unresolved
