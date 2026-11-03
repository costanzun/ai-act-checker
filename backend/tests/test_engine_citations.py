"""Every provision ID used by the engine must be well formed and resolve in the corpus."""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from app.engine import FactSheet, all_citation_ids, checklist_for, classify, obligations_for
from tests.test_engine_obligations import CV
from tests.test_engine_rules import ANNEX_III_CASES, PROHIBITION_CASES, sheet

CORPUS_DIR = Path(__file__).resolve().parents[2] / "data" / "corpus"

ID_RE = re.compile(
    r"^(art:\d+[a-z]*(\.\d+[a-z]*)?(\.[a-z]+)?(\.[ivx]+)?"
    r"|annex:[IVX]+(\.[AB])?(\.\d+)?(\.[a-z])?"
    r"|rec:\d+)$"
)


def _sample_sheets() -> list[FactSheet]:
    out = [FactSheet(), sheet(), sheet(role=None, **CV)]
    out += [sheet(**ov) for _, ov, _, _ in PROHIBITION_CASES]
    out += [sheet(annex_iii_area=a, art63__profiling_of_natural_persons=True) for a, _ in ANNEX_III_CASES]
    out += [
        sheet(annex_i_product=p, safety_component=True, annex_i_third_party_assessment=True)
        for p in ("medical_devices", "machinery", "vehicles", "civil_aviation", "other_regulated_product")
    ]
    out += [
        sheet(role=None, transparency__interacts_with_natural_persons=True, transparency__generates_synthetic_content=True,
              transparency__deepfake=True, transparency__public_interest_text=True, biometric__emotion_recognition=True),
        sheet(role=None, gpai__is_gpai_model=True, gpai__provider_of_model=True, gpai__systemic_risk=True),
        sheet(gpai__integrates_third_party_gpai=True, gpai__substantially_modifies_model=False),
        sheet(annex_iii_area="4a_recruitment_selection", decision_impact="supports_human_decision",
              art63__narrow_procedural_task=True, art63__profiling_of_natural_persons=False),
        sheet(is_ai_system=False), sheet(free_open_source_licence=True),
    ]
    return out


def test_ids_well_formed():
    bad = sorted(i for i in all_citation_ids() if not ID_RE.match(i))
    assert not bad, bad


def test_every_emitted_citation_is_registered():
    known = all_citation_ids()
    for f in _sample_sheets():
        c = classify(f)
        emitted = {x for fd in c.findings for x in fd.citations}
        ob = obligations_for(c, f)
        emitted |= {x for o in ob for x in o.citations}
        emitted |= {x for it in checklist_for(ob) for x in it.citations}
        emitted |= {x for m in c.applies_from for x in m.citations}
        assert emitted <= known, sorted(emitted - known)


def test_every_citation_resolves_in_corpus():
    if not (CORPUS_DIR / "en.json").exists():
        pytest.skip(f"corpus not built yet ({CORPUS_DIR / 'en.json'} missing); run scripts/build_corpus.py")
    try:
        from app.corpus.store import CorpusStore
    except ImportError as exc:  # pragma: no cover
        pytest.skip(f"app.corpus.store not available: {exc}")
    store = CorpusStore(CORPUS_DIR)
    missing = sorted(i for i in all_citation_ids() if not store.exists(i))
    assert not missing, f"{len(missing)} citation IDs do not resolve: {missing}"
