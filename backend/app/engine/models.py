"""Pydantic models of the engine API (docs/CONTRACTS.md §5)."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

Tier = Literal["prohibited", "high_risk", "limited_risk", "minimal_risk", "out_of_scope"]
Confidence = Literal["high", "medium", "low"]
FindingKind = Literal[
    "prohibition",
    "high_risk_annex_iii",
    "high_risk_annex_i",
    "derogation_6_3",
    "transparency",
    "gpai",
    "scope",
    "not_ai_system",
    "note",
]
Bilingual = dict[str, str]


class Milestone(BaseModel):
    id: str
    date: str
    what: Bilingual
    citations: list[str]
    status: Literal["in_force", "upcoming"]


class Finding(BaseModel):
    rule_id: str
    kind: FindingKind
    title: Bilingual
    rationale: Bilingual
    citations: list[str]
    facts_used: list[str]
    decisive: bool = False


class Classification(BaseModel):
    tier: Tier
    confidence: Confidence
    findings: list[Finding]
    overlays: dict[str, list[str]] = Field(default_factory=dict)
    role: Literal["provider", "deployer", "both", "other", "unknown"]
    applies_from: list[Milestone] = Field(default_factory=list)
    unresolved: list[str] = Field(default_factory=list)
    assumptions: list[Bilingual] = Field(default_factory=list)


class Question(BaseModel):
    id: str
    fact_path: str
    text: Bilingual
    why: Bilingual
    type: Literal["single", "boolean", "text"]
    options: list[dict[str, Any]]
    impact: float


class Obligation(BaseModel):
    id: str
    role: Literal["provider", "deployer", "both"]
    category: Literal[
        "governance", "documentation", "data", "transparency", "oversight", "registration", "monitoring", "literacy", "other"
    ]
    title: Bilingual
    summary: Bilingual
    citations: list[str]
    applies_from: str | None
    priority: Literal["must", "should"]


class ChecklistItem(BaseModel):
    id: str
    title: Bilingual
    description: Bilingual
    citations: list[str]
    obligation_ids: list[str]
    template_hint: Bilingual | None = None
