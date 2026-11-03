"""Tests for obligations, checklist and timeline."""

from __future__ import annotations

from datetime import date

from app.engine import checklist_for, classify, obligations_for, timeline
from app.engine.checklist import CATALOG
from app.engine.obligations import obligation_ids
from tests.test_engine_rules import sheet

CV = dict(annex_iii_area="4a_recruitment_selection", decision_impact="materially_influences",
          art63__profiling_of_natural_persons=True)


def obls(**kw):
    f = sheet(**kw)
    return obligations_for(classify(f), f)


def ids(ob) -> set[str]:
    return {o.id for o in ob}


def test_provider_and_deployer_sets_differ():
    p = ids(obls(role="provider", **CV))
    d = ids(obls(role="deployer", **CV))
    assert {"hr-p-art9", "hr-p-art11", "hr-p-art17", "hr-p-art43", "hr-p-art47", "hr-p-art49", "hr-p-art72",
            "hr-p-art73"} <= p
    assert {"hr-d-art26.1", "hr-d-art26.2", "hr-d-art26.5", "hr-d-art26.6", "hr-d-art26.7", "hr-d-art26.11",
            "hr-d-art86"} <= d
    assert not any(i.startswith("hr-d-") for i in p)
    assert not any(i.startswith("hr-p-") for i in d)
    assert "lit-art4" in p and "lit-art4" in d


def test_unknown_or_both_role_gets_both_sets():
    b = ids(obls(role=None, **CV))
    assert "hr-p-art9" in b and "hr-d-art26.1" in b


def test_high_risk_dates():
    for o in obls(role="provider", **CV):
        if o.id.startswith("hr-"):
            assert o.applies_from == "2027-12-02"
    ob = obls(role="provider", annex_i_product="medical_devices", safety_component=True,
              annex_i_third_party_assessment=True)
    assert {o.applies_from for o in ob if o.id.startswith("hr-")} == {"2028-08-02"}
    a43 = next(o for o in ob if o.id == "hr-p-art43")
    assert "art:43.3" in a43.citations
    assert "hr-p-art49" not in ids(ob)  # Art. 49(1) registration concerns Annex III systems


def test_conformity_route_biometrics_vs_other_annex_iii():
    bio = next(o for o in obls(annex_iii_area="1c_emotion_recognition", art63__profiling_of_natural_persons=True)
               if o.id == "hr-p-art43")
    assert {"annex:VI", "annex:VII"} <= set(bio.citations)
    other = next(o for o in obls(**CV) if o.id == "hr-p-art43")
    assert "annex:VII" not in other.citations


def test_other_dates():
    lit = next(o for o in obls() if o.id == "lit-art4")
    assert lit.applies_from == "2025-02-02"
    chat = obls(transparency__interacts_with_natural_persons=True, transparency__obvious_to_users_it_is_ai=False)
    assert next(o for o in chat if o.id == "tr-p-art50.1").applies_from == "2026-08-02"
    gp = obls(gpai__is_gpai_model=True, gpai__provider_of_model=True)
    assert {o.applies_from for o in gp if o.id.startswith("gpai-")} == {"2025-08-02"}
    old = obls(social_scoring=True)
    assert next(o for o in old if o.id == "pro-art5").applies_from == "2025-02-02"
    new = obls(transparency__generates_synthetic_content=True, nudify_or_sexual_abuse_material=True)
    assert next(o for o in new if o.id == "pro-art5").applies_from == "2026-12-02"
    assert "pro-art99" in ids(new)


def test_transparency_split_by_role():
    kw = dict(transparency__generates_synthetic_content=True, transparency__deepfake=True)
    assert ids(obls(role="provider", **kw)) & {"tr-p-art50.2", "tr-d-art50.4"} == {"tr-p-art50.2"}
    assert ids(obls(role="deployer", **kw)) & {"tr-p-art50.2", "tr-d-art50.4"} == {"tr-d-art50.4"}


def test_fria_conditions():
    assert "hr-d-art27" not in ids(obls(role="deployer", public_body_or_public_service=False, **CV))
    assert "hr-d-art27" in ids(obls(role="deployer", public_body_or_public_service=True, **CV))
    credit = obls(role="deployer", public_body_or_public_service=False, annex_iii_area="5b_creditworthiness",
                  art63__profiling_of_natural_persons=True)
    assert "hr-d-art27" in ids(credit)
    unknown = next(o for o in obls(role="deployer", public_body_or_public_service=None, **CV) if o.id == "hr-d-art27")
    assert unknown.priority == "should"


def test_derogation_obligations():
    ob = obls(annex_iii_area="4a_recruitment_selection", decision_impact="supports_human_decision",
              art63__narrow_procedural_task=True, art63__profiling_of_natural_persons=False)
    assert {"der-p-art6.4", "der-p-art49.2", "lit-art4"} <= ids(ob)
    assert not any(i.startswith("hr-") for i in ids(ob))


def test_section_b_only_sectoral():
    ob = obls(annex_i_product="vehicles", safety_component=True, annex_i_third_party_assessment=True)
    assert ids(ob) == {"hr-annex-i-b-sectoral"}


def test_gpai_open_source_exemption_and_systemic():
    os_ = ids(obls(free_open_source_licence=True, gpai__is_gpai_model=True, gpai__provider_of_model=True))
    assert "gpai-art53.1.a" not in os_ and "gpai-art53.1.c" in os_
    sr = ids(obls(free_open_source_licence=True, gpai__is_gpai_model=True, gpai__provider_of_model=True,
                  gpai__systemic_risk=True))
    assert {"gpai-art53.1.a", "gpai-art55.1.a", "gpai-art52.1"} <= sr


def test_out_of_scope_and_minimal():
    assert obls(is_ai_system=False) == []
    assert ids(obls()) == {"lit-art4", "min-art95"}


def test_obligations_bilingual():
    for o in obls(role=None, **CV):
        assert set(o.title) == {"en", "it"} and set(o.summary) == {"en", "it"}
        assert o.citations


def test_checklist():
    ob = obls(role="provider", **CV)
    cl = checklist_for(ob)
    cids = {c.id for c in cl}
    assert {"doc-technical-documentation", "doc-risk-management-file", "doc-qms", "doc-eu-declaration",
            "doc-post-market-plan", "doc-serious-incident-procedure", "doc-ai-literacy-programme"} <= cids
    present = ids(ob)
    for c in cl:
        assert set(c.obligation_ids) <= present and c.citations and c.template_hint
    gp = checklist_for(obls(gpai__is_gpai_model=True, gpai__provider_of_model=True))
    assert {"doc-gpai-technical-documentation", "doc-gpai-copyright-policy", "doc-gpai-training-summary"} <= {
        c.id for c in gp}


def test_checklist_references_known_obligations():
    known = obligation_ids()
    for it in CATALOG:
        assert set(it.obligation_ids) <= known, it.id


def test_timeline_status():
    tl = timeline(date(2026, 11, 3))
    by = {m.id: m for m in tl}
    assert by["general-application"].status == "in_force"
    assert by["new-prohibitions-and-marking-legacy"].status == "upcoming"
    assert by["high-risk-annex-iii"].date == "2027-12-02"
    assert by["high-risk-annex-i"].date == "2028-08-02"
    assert timeline(date(2029, 1, 1))[-3].status == "in_force"
    assert [m.date for m in tl] == sorted(m.date for m in tl)
