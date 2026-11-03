"""API-level schemas (CONTRACTS §7): request, assessment, metrics, SSE event payloads."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Literal
from uuid import uuid4

from pydantic import BaseModel, Field

from app.engine.facts import FactSheet
from app.engine.models import ChecklistItem, Classification, Milestone, Obligation, Question

Language = Literal["en", "it"]

LAW_AS_OF = "2026-07-27"
LAW_CHECKED_AT = "2026-11-03"
CELEX = "02024R1689-20260727"

DISCLAIMER = {
    "en": (
        "This assessment is generated automatically from the text of Regulation (EU) 2024/1689 as "
        "consolidated on 27 July 2026 (including Regulation (EU) 2026/1744). It is an orientation tool, "
        "not legal advice, and it does not replace an assessment by a qualified lawyer. Verify every "
        "citation against the official text before relying on it."
    ),
    "it": (
        "Questa valutazione è generata automaticamente dal testo del Regolamento (UE) 2024/1689 nella "
        "versione consolidata al 27 luglio 2026 (incluso il Regolamento (UE) 2026/1744). È uno strumento "
        "di orientamento, non costituisce consulenza legale e non sostituisce la valutazione di un "
        "avvocato. Verificare ogni citazione sul testo ufficiale prima di farvi affidamento."
    ),
}


class Answer(BaseModel):
    fact_path: str
    value: Any


class AssessRequest(BaseModel):
    description: str = Field(..., min_length=20, max_length=6000)
    language: Language = "en"
    session_id: str | None = None
    facts: FactSheet | None = None
    answers: list[Answer] = Field(default_factory=list)
    asked: list[str] = Field(default_factory=list, description="Question ids already asked in earlier rounds")
    round: int = Field(0, ge=0, le=5)
    provider: str | None = None
    model: str | None = None


class ModelInfo(BaseModel):
    provider: str
    model: str


class Metrics(BaseModel):
    latency_ms: int = 0
    llm_calls: int = 0
    input_tokens: int = 0
    output_tokens: int = 0
    cost_usd: float = 0.0
    cached: bool = False
    stripped_citations: int = Field(0, description="Citation tokens produced by the LLM that were not allowed and were removed")


class RelatedProvision(BaseModel):
    id: str
    label: str
    why: dict[str, str]


class Assessment(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat(timespec="seconds"))
    language: Language = "en"
    law_as_of: str = LAW_AS_OF
    checked_at: str = LAW_CHECKED_AT
    model: ModelInfo
    description: str
    facts: FactSheet
    classification: Classification
    summary: dict[str, str] | None = Field(None, description="One-sentence bilingual summary for the tier hero")
    reasoning_md: str
    obligations: list[Obligation]
    checklist: list[ChecklistItem]
    related_provisions: list[RelatedProvision] = Field(default_factory=list)
    uncertainties: list[dict[str, str]] = Field(default_factory=list)
    disclaimer: dict[str, str] = Field(default_factory=lambda: dict(DISCLAIMER))
    metrics: Metrics = Field(default_factory=Metrics)


class QuestionsPayload(BaseModel):
    questions: list[Question]
    facts: FactSheet
    round: int
    session_id: str
    asked: list[str]


class MetaResponse(BaseModel):
    law_as_of: str = LAW_AS_OF
    checked_at: str = LAW_CHECKED_AT
    celex: str = CELEX
    amending_acts: list[dict[str, str]]
    provider: str
    model: str
    timeline: list[Milestone]
    disclaimer: dict[str, str] = Field(default_factory=lambda: dict(DISCLAIMER))
    languages: list[str] = Field(default_factory=lambda: ["en", "it"])
