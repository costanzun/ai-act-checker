""""What would change the answer": counterfactuals over the facts the result depends on.

Read-only over the rule engine: it never alters the classification. For each fact the
result hinges on (facts read by decisive findings or by the Art. 6(3) derogation, plus
the unresolved facts) it probes the other values of that fact with the same optimistic
completion the question selector uses (``rules.probe``) and keeps the ones that can move
the tier. Each item names the question, the current answer and the answer that could
change the tier, so the UI can offer it as a one-click re-run.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel

from .facts import FactSheet
from .models import Classification, Tier
from .questions import _BY_PATH, REGISTRY, _gate_open
from .rules import DEROGATION_RULE, domain, evaluate, probe

Bi = dict[str, str]

MAX_ITEMS = 4
MAX_UNRESOLVED = 2
_UNKNOWN = {"en": "Not stated", "it": "Non indicato"}
# Many-valued facts: only the "none of these" alternative is a meaningful counterfactual.
_MANY = 5
_SEVERITY = {"prohibited": 4, "high_risk": 3, "limited_risk": 2, "minimal_risk": 1, "out_of_scope": 0}


class WhatIf(BaseModel):
    fact_path: str
    question: Bi
    why: Bi
    current: Bi
    current_value: Any = None
    answer: Bi
    value: Any = None
    tier: Tier
    unresolved: bool
    actionable: bool = True


def _label(path: str, value: Any) -> Bi:
    e = _BY_PATH.get(path)
    if e is not None:
        for o in e.options:
            if o["value"] == value:
                return dict(o["label"])
    if value is True:
        return {"en": "Yes", "it": "Sì"}
    if value is False:
        return {"en": "No", "it": "No"}
    return {"en": str(value), "it": str(value)}


def _group(path: str) -> str:
    """The Art. 6(3) derogation (its conditions and the decision-impact gate) is one point for the reader."""
    return "art63" if path.startswith("art63.") or path == "decision_impact" else path


_LOW_TIER_PROBES = ["transparency.interacts_with_natural_persons", "transparency.generates_synthetic_content"]


def _candidate_paths(facts: FactSheet, c: Classification) -> list[tuple[str, bool]]:
    """(path, unresolved) in priority order: up to two unresolved facts, then decisive ones."""
    out: list[tuple[str, bool]] = []
    groups: set[str] = set()
    for p in c.unresolved:
        if len(out) >= MAX_UNRESOLVED:
            break
        if p in _BY_PATH and p != "role" and _group(p) not in groups:
            out.append((p, True))
            groups.add(_group(p))
    known: list[str] = []
    for fd in c.findings:
        if fd.decisive:
            known += fd.facts_used
    if any(fd.kind in ("high_risk_annex_iii", "derogation_6_3") for fd in c.findings):
        known += sorted(DEROGATION_RULE.paths())
    if c.tier in ("minimal_risk", "limited_risk"):
        known += _LOW_TIER_PROBES
    order = {e.path: i for i, e in enumerate(REGISTRY)}
    # many-valued facts (e.g. the Annex III area) give the bluntest counterfactual: list them last
    many = lambda x: len(_BY_PATH[x].options) >= _MANY if x in _BY_PATH else False
    for p in sorted(dict.fromkeys(known), key=lambda x: (many(x), order.get(x, 999))):
        if _group(p) in groups or p not in _BY_PATH or p == "role":
            continue
        if facts.get_path(p) is None or not _gate_open(facts, _BY_PATH[p]):
            continue
        out.append((p, False))
        groups.add(_group(p))
    return out


_ANNEX_III_ANY = {
    "en": "Used for an Annex III purpose (e.g. hiring, credit scoring, education, essential services)",
    "it": "Usato per una finalità dell'allegato III (ad es. assunzioni, merito creditizio, istruzione, servizi essenziali)",
}


def what_would_change(facts: FactSheet, c: Classification, limit: int = MAX_ITEMS) -> list[WhatIf]:
    base = evaluate(facts)
    items: list[WhatIf] = []
    for path, unresolved in _candidate_paths(facts, c):
        current = facts.get_path(path)
        values = [v for v in domain(path) if v != current]
        if len(values) >= _MANY:
            values = [v for v in values if v == "none"]
        best: tuple[int, Any, str] | None = None
        for v in values:
            tier = probe(facts, path, v).tier
            if tier == base.tier:
                continue
            score = abs(_SEVERITY[tier] - _SEVERITY[base.tier])
            if best is None or score > best[0]:
                best = (score, v, tier)
        if best is None:
            continue
        _, v, tier = best
        e = _BY_PATH[path]
        items.append(
            WhatIf(
                fact_path=path,
                question=dict(e.text),
                why=dict(e.why),
                current=_label(path, current) if current is not None else dict(_UNKNOWN),
                current_value=current,
                answer=_label(path, v),
                value=v,
                tier=tier,  # type: ignore[arg-type]
                unresolved=unresolved,
            )
        )
        if len(items) >= limit:
            break
    if (
        len(items) < limit
        and base.tier in ("minimal_risk", "limited_risk")
        and facts.annex_iii_area == "none"
        and facts.is_ai_system is not False
    ):
        e = _BY_PATH["annex_iii_area"]
        items.append(
            WhatIf(
                fact_path="annex_iii_area",
                question=dict(e.text),
                why=dict(e.why),
                current=_label("annex_iii_area", "none"),
                current_value="none",
                answer=dict(_ANNEX_III_ANY),
                tier="high_risk",
                unresolved=False,
                actionable=False,
            )
        )
    return items
