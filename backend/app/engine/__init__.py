"""Rule engine for the EU AI Act (Reg. (EU) 2024/1689 as amended by Reg. (EU) 2026/1744).

Public API: see docs/CONTRACTS.md §5.
"""

from __future__ import annotations

from .checklist import checklist_citation_ids, checklist_for
from .facts import FactSheet
from .models import (
    ChecklistItem,
    Classification,
    Confidence,
    Finding,
    Milestone,
    Obligation,
    Question,
    Tier,
)
from .obligations import obligation_citation_ids, obligations_for
from .questions import next_questions
from .rules import classify, rule_citation_ids
from .timeline import timeline, timeline_citation_ids


def all_citation_ids() -> set[str]:
    """Every provision ID used anywhere in the engine (rules, obligations, checklist, timeline)."""
    return rule_citation_ids() | obligation_citation_ids() | checklist_citation_ids() | timeline_citation_ids()


__all__ = [
    "ChecklistItem",
    "Classification",
    "Confidence",
    "FactSheet",
    "Finding",
    "Milestone",
    "Obligation",
    "Question",
    "Tier",
    "all_citation_ids",
    "checklist_for",
    "classify",
    "next_questions",
    "obligations_for",
    "timeline",
]
