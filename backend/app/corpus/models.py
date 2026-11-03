"""Pydantic models for the legal corpus (see docs/CONTRACTS.md sections 1-3)."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

ProvisionType = Literal[
    "article", "paragraph", "point", "annex", "annex_point", "recital", "guidance"
]


class Amendment(BaseModel):
    """Amendment metadata of a provision (consolidation marker such as ``M1``)."""

    marker: str
    kind: Literal["replaced", "inserted", "deleted"]
    by: str


class AmendingAct(BaseModel):
    """An act that amended the base regulation and is marked in the consolidation."""

    celex: str
    marker: str
    short_title: str
    oj_date: str | None = None
    in_force: str | None = None


class Provision(BaseModel):
    """One addressable unit of the law (article, paragraph, point, annex item, recital).

    ``text`` is the node's own text. Additive fields beyond the contract:

    * ``body``: unnumbered text of an article/annex that precedes its numbered
      items (e.g. the chapeau of Art. 3 or the whole text of Art. 105).
    * ``text_after``: text that follows the node's children (the closing
      sub-paragraph of Art. 5(1), the last sentence of Art. 4a(2), ...).
    """

    model_config = ConfigDict(extra="allow")

    id: str
    type: ProvisionType
    label: str
    parent_id: str | None = None
    children: list[str] = Field(default_factory=list)
    article: int | str | None = None
    paragraph: str | None = None
    point: str | None = None
    annex: str | None = None
    recital: int | None = None
    chapter: str | None = None
    chapter_title: str | None = None
    section: str | None = None
    section_title: str | None = None
    title: str | None = None
    text: str = ""
    body: str | None = None
    text_after: str | None = None
    original_text: str | None = None
    amendment: Amendment | None = None
    order: int = 0


class CorpusMeta(BaseModel):
    """Corpus-level metadata (``meta`` object of the corpus JSON)."""

    model_config = ConfigDict(extra="allow")

    celex: str
    language: Literal["en", "it"]
    consolidated_as_of: str
    retrieved_at: str
    source_url: str
    eurlex_url: str
    amending_acts: list[AmendingAct] = Field(default_factory=list)
    counts: dict[str, int] = Field(default_factory=dict)
    extra: dict[str, Any] | None = None
