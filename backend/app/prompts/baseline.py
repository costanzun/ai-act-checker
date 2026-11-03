"""Baseline prompt for the evaluation only: pure LLM + retrieved provisions.

This is the approach most "AI Act chatbots" take. It is included so the eval
can quantify what the deterministic rule engine adds (tier accuracy and
citation validity). It is not used in the product flow.
"""

from __future__ import annotations

SYSTEM = """You are an expert on the EU Artificial Intelligence Act (Regulation (EU) 2024/1689 as amended by Regulation (EU) 2026/1744). Classify the AI system described by the user.

Tiers: "prohibited" (Article 5), "high_risk" (Article 6 with Annex I or Annex III), "limited_risk" (only transparency obligations under Article 50), "minimal_risk" (none of the above), "out_of_scope" (not an AI system under Article 3(1), or excluded by Article 2).
Overlays (may be empty): "transparency_art50" when Article 50 duties attach in addition to the tier; "gpai" when the user is a provider of a general-purpose AI model.
Role: "provider", "deployer", "both", "other" or "unknown".

Use the retrieved provisions as your primary source. Cite provisions with their IDs exactly as given (e.g. art:6.2, annex:III.4.a). Output exactly one JSON object:
{"tier": "...", "overlays": [...], "role": "...", "citations": ["art:...", ...], "reasoning": "3-5 sentences", "confidence": "high|medium|low"}
No prose outside the JSON."""

USER = """Description:
\"\"\"
{description}
\"\"\"

Retrieved provisions:
{context}

Return the JSON object now."""


def baseline_messages(description: str, context_blocks: dict[str, str]) -> list[dict[str, str]]:
    ctx = "\n\n".join(f"[{pid}] {' '.join(t.split())[:900]}" for pid, t in context_blocks.items()) or "(none)"
    return [
        {"role": "system", "content": SYSTEM},
        {"role": "user", "content": USER.format(description=description.strip(), context=ctx)},
    ]
