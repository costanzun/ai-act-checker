"""Prompt templates for the EU AI Act Checker.

Three LLM tasks exist in the product:

1. ``extract``   — turn a plain-language description into a FactSheet (JSON).
2. ``narrative`` — write the cited reasoning text, constrained to the
                   deterministic engine's findings and an allow-list of IDs.
3. ``baseline``  — the "pure LLM + retrieval" classifier used only in the
                   evaluation as a comparison point.

The question wording is produced by the rule engine, not by an LLM, so that
the clarifying step is deterministic and testable.
"""

from .baseline import baseline_messages
from .extract import extract_messages
from .narrative import narrative_messages
from .schema import render_compact_schema

__all__ = ["extract_messages", "narrative_messages", "baseline_messages", "render_compact_schema"]
