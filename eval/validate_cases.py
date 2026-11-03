"""Validate eval/cases.yaml against the eval-case schema (docs/CONTRACTS.md §9).

Run from anywhere:
    backend/.venv/bin/python eval/validate_cases.py [path/to/cases.yaml]

Checks
- required keys and enumerations (language, source, role, tier, overlays, difficulty);
- ids unique and kebab-case;
- `facts` uses only valid FactSheet dotted paths and values
  (converted to a nested dict and passed to FactSheet.model_validate);
- `facts.role` agrees with the case `role`; overlay/fact consistency for gpai;
- `expected_citations` well-formed (CONTRACTS §1) and, if data/corpus/en.json exists,
  that every id resolves via app.corpus.store.CorpusStore (skipped otherwise).
Exit code 0 when valid, 1 otherwise.
"""

from __future__ import annotations

import re
import sys
from collections import Counter
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, ValidationError

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.engine.facts import FactSheet  # noqa: E402

TIERS = {"prohibited", "high_risk", "limited_risk", "minimal_risk", "out_of_scope"}
OVERLAYS = {"transparency_art50", "gpai"}
SOURCES = {"annex_iii", "art5", "commission_guidelines", "art50", "gpai", "edge"}
ROLES = {"provider", "deployer", "both", "other", "unknown"}
LANGS = {"en", "it"}
DIFFICULTY = {"easy", "medium", "hard"}
REQUIRED = [
    "id", "title", "description", "language", "source", "role", "expected_tier",
    "expected_overlays", "expected_citations", "should_ask", "facts", "notes", "difficulty",
]
ID_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
ROMAN = r"(?:I|II|III|IV|V|VI|VII|VIII|IX|X|XI|XII|XIII|XIV)"
CITATION_RE = re.compile(
    r"^(?:"
    r"art:\d+[a-z]?(?:\.\d+[a-z]?(?:\.[a-z]{1,2}(?:\.[ivx]+)?)?)?"  # art:5 / art:5.1a / art:5.1.ba / art:5.1.h.i
    rf"|annex:{ROMAN}(?:\.[A-Z])?(?:\.\d+(?:\.[a-z]{{1,2}})?)?"  # annex:III / annex:III.4.a / annex:I.A.11
    r"|rec:\d+"
    r"|guid:[a-z0-9-]+(?:\.[0-9a-z.]+)?"
    r")$"
)


def valid_paths(model: type[BaseModel], prefix: str = "") -> set[str]:
    out: set[str] = set()
    for name, field in model.model_fields.items():
        ann = field.annotation
        if isinstance(ann, type) and issubclass(ann, BaseModel):
            out |= valid_paths(ann, f"{prefix}{name}.")
        else:
            out.add(f"{prefix}{name}")
    return out


FACT_PATHS = valid_paths(FactSheet)


def to_nested(flat: dict[str, Any]) -> dict[str, Any]:
    nested: dict[str, Any] = {}
    for key, value in flat.items():
        node = nested
        parts = key.split(".")
        for part in parts[:-1]:
            node = node.setdefault(part, {})
        node[parts[-1]] = value
    return nested


def load_corpus():
    corpus_file = ROOT / "data" / "corpus" / "en.json"
    if not corpus_file.exists():
        return None, f"SKIP citation resolution: {corpus_file.relative_to(ROOT)} not found"
    try:
        from app.corpus.store import CorpusStore
    except ImportError as exc:  # corpus built but store not yet available
        return None, f"SKIP citation resolution: cannot import app.corpus.store ({exc})"
    return CorpusStore(ROOT / "data" / "corpus"), None


def validate(path: Path) -> int:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    errors: list[str] = []
    if not isinstance(data, list):
        print(f"FAIL: {path} must contain a YAML list of cases")
        return 1

    store, skip_msg = load_corpus()
    ids = Counter(c.get("id") for c in data if isinstance(c, dict))
    for dup, n in ids.items():
        if n > 1:
            errors.append(f"duplicate id {dup!r} ({n}x)")

    for i, case in enumerate(data):
        cid = case.get("id", f"#{i}") if isinstance(case, dict) else f"#{i}"

        def err(msg: str) -> None:
            errors.append(f"[{cid}] {msg}")

        if not isinstance(case, dict):
            err("case is not a mapping")
            continue
        for key in REQUIRED:
            if key not in case:
                err(f"missing key {key!r}")
        extra = set(case) - set(REQUIRED)
        if extra:
            err(f"unknown keys {sorted(extra)}")
        if not ID_RE.match(str(case.get("id", ""))):
            err("id must be kebab-case")
        for key in ("title", "description", "notes"):
            if not isinstance(case.get(key), str) or not case.get(key, "").strip():
                err(f"{key} must be a non-empty string")
        if case.get("language") not in LANGS:
            err(f"language {case.get('language')!r} not in {sorted(LANGS)}")
        if case.get("source") not in SOURCES:
            err(f"source {case.get('source')!r} not in {sorted(SOURCES)}")
        if case.get("role") not in ROLES:
            err(f"role {case.get('role')!r} not in {sorted(ROLES)}")
        if case.get("expected_tier") not in TIERS:
            err(f"expected_tier {case.get('expected_tier')!r} not in {sorted(TIERS)}")
        if case.get("difficulty") not in DIFFICULTY:
            err(f"difficulty {case.get('difficulty')!r} not in {sorted(DIFFICULTY)}")
        if not isinstance(case.get("should_ask"), bool):
            err("should_ask must be a boolean")

        overlays = case.get("expected_overlays")
        if not isinstance(overlays, list) or not set(overlays) <= OVERLAYS:
            err(f"expected_overlays must be a subset of {sorted(OVERLAYS)}")
            overlays = []
        if len(set(overlays)) != len(overlays):
            err("expected_overlays has duplicates")

        cites = case.get("expected_citations")
        if not isinstance(cites, list) or not cites:
            err("expected_citations must be a non-empty list")
            cites = []
        elif not 1 <= len(cites) <= 5:
            err(f"expected_citations should list 1-5 key ids (has {len(cites)})")
        for cite in cites:
            if not isinstance(cite, str) or not CITATION_RE.match(cite):
                err(f"malformed citation id {cite!r}")
            elif store is not None and not store.exists(cite):
                err(f"citation {cite!r} does not resolve in corpus")

        facts = case.get("facts")
        if not isinstance(facts, dict) or not facts:
            err("facts must be a non-empty mapping of dotted paths")
            continue
        unknown = sorted(k for k in facts if k not in FACT_PATHS)
        if unknown:
            err(f"unknown FactSheet paths {unknown}")
        try:
            sheet = FactSheet.model_validate(to_nested(facts))
        except ValidationError as exc:
            for e in exc.errors():
                err(f"facts.{'.'.join(map(str, e['loc']))}: {e['msg']}")
            continue

        role = case.get("role")
        if sheet.role is None:
            err("facts.role must be set (ground truth)")
        elif role in ROLES - {"unknown"} and sheet.role != role:
            err(f"facts.role {sheet.role!r} != case role {role!r}")
        if sheet.is_ai_system is None:
            err("facts.is_ai_system must be set (ground truth)")
        if ("gpai" in overlays) != bool(sheet.gpai.is_gpai_model and sheet.gpai.provider_of_model):
            err("gpai overlay must match facts gpai.is_gpai_model & gpai.provider_of_model")
        if case.get("expected_tier") == "out_of_scope" and not (
            sheet.is_ai_system is False
            or sheet.in_eu_scope is False
            or (sheet.scope_exclusion not in (None, "none"))
        ):
            err("out_of_scope needs is_ai_system=false, in_eu_scope=false or a scope_exclusion")
        if case.get("expected_tier") == "high_risk" and sheet.annex_iii_area in (None, "none") and (
            sheet.annex_i_product in (None, "none")
        ):
            err("high_risk needs an annex_iii_area or annex_i_product in facts")

    # ---- report ---------------------------------------------------------------
    n = len(data)
    print(f"Validated {n} cases from {path}")
    for label, key in (("source", "source"), ("tier", "expected_tier"), ("role", "role"),
                       ("language", "language"), ("difficulty", "difficulty")):
        counts = Counter(c.get(key) for c in data if isinstance(c, dict))
        print(f"  {label:<10} " + ", ".join(f"{k}={v}" for k, v in sorted(counts.items())))
    asks = [c["id"] for c in data if isinstance(c, dict) and c.get("should_ask") is True]
    print(f"  should_ask={len(asks)}: {', '.join(asks)}")
    print(skip_msg or f"Citation resolution: checked against corpus ({ROOT / 'data/corpus'})")
    if errors:
        print(f"FAIL: {len(errors)} error(s)")
        for e in errors:
            print("  - " + e)
        return 1
    print("OK")
    return 0


if __name__ == "__main__":
    target = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "eval" / "cases.yaml"
    sys.exit(validate(target))
