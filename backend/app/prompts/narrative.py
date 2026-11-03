"""Narrative prompt: write the cited reasoning, constrained to the engine's findings.

The engine has already decided the tier and the citations. The model's job is
to explain that decision clearly to a compliance manager in the chosen
language, citing only provision IDs from an allow-list. The server validates
every ``[[id]]`` token afterwards and removes unknown ones, so a hallucinated
citation can never reach the UI.
"""

from __future__ import annotations

import json
from typing import Any

LANG_NAME = {"en": "English", "it": "Italian"}

SYSTEM = """You write the "Reasoning" section of an EU AI Act (Regulation (EU) 2024/1689, as amended by Regulation (EU) 2026/1744) assessment for a compliance manager who is not a lawyer.

You receive: (a) the facts about the system, (b) the classification already decided by a deterministic rule engine, with its findings and their citations, (c) excerpts of the cited provisions, (d) the list of provision IDs you are allowed to cite.

Hard rules
1. Never change, soften or extend the classification. The tier, the overlays and the role are fixed. Do not introduce legal conclusions that are not in the findings.
2. Every sentence that states what the law says or requires must end with at least one citation token of the form [[art:6.2]], [[annex:III.4.a]] or [[rec:57]], using ONLY IDs from the allowed list. Never invent IDs. Never write article numbers in any other form (no "Article 6(2)" without the token).
3. Write in {language}. Plain, precise, calm. No marketing, no first person, no "as an AI". Use the system's own terms from the description.
4. Length 120–220 words, 2–4 short paragraphs, Markdown without headings or lists.
   - Paragraph 1: the result and the decisive reason (the finding marked decisive).
   - Paragraph 2: why neighbouring outcomes do not apply when that is informative (e.g. why it is not prohibited, why the Article 6(3) derogation does or does not apply, which Article 50 duties attach).
   - Last paragraph: what remains uncertain, naming the assumptions made and what would change the result. If nothing is uncertain, say the facts given were sufficient.
5. Mention the date from which the relevant obligations apply, as given in the classification, with its citation.
6. Do not repeat the obligations list or the checklist; they are shown separately.

Output only the Markdown text."""

USER = """Language: {language}

Description (verbatim from the user):
\"\"\"
{description}
\"\"\"

Facts (JSON):
{facts}

Classification decided by the rule engine (JSON):
{classification}

Excerpts of the cited provisions:
{excerpts}

Allowed citation IDs (use only these): {allowed}

Write the reasoning now."""


def _excerpt_block(excerpts: dict[str, str], max_chars: int = 700) -> str:
    parts = []
    for pid, text in excerpts.items():
        t = " ".join(text.split())
        if len(t) > max_chars:
            t = t[: max_chars - 1].rsplit(" ", 1)[0] + "…"
        parts.append(f"[{pid}] {t}")
    return "\n\n".join(parts) if parts else "(none)"


def narrative_messages(
    *,
    description: str,
    facts: dict[str, Any],
    classification: dict[str, Any],
    excerpts: dict[str, str],
    allowed_ids: list[str],
    language: str = "en",
) -> list[dict[str, str]]:
    lang = LANG_NAME.get(language, "English")
    slim = {
        "tier": classification.get("tier"),
        "confidence": classification.get("confidence"),
        "role": classification.get("role"),
        "overlays": classification.get("overlays"),
        "applies_from": classification.get("applies_from"),
        "assumptions": [a.get(language) or a.get("en") for a in classification.get("assumptions", [])],
        "unresolved": classification.get("unresolved"),
        "findings": [
            {
                "title": (f.get("title") or {}).get(language) or (f.get("title") or {}).get("en"),
                "rationale": (f.get("rationale") or {}).get(language) or (f.get("rationale") or {}).get("en"),
                "citations": f.get("citations"),
                "decisive": f.get("decisive"),
            }
            for f in classification.get("findings", [])
        ],
    }
    return [
        {"role": "system", "content": SYSTEM.format(language=lang)},
        {
            "role": "user",
            "content": USER.format(
                language=lang,
                description=description.strip(),
                facts=json.dumps(facts, ensure_ascii=False, indent=1),
                classification=json.dumps(slim, ensure_ascii=False, indent=1),
                excerpts=_excerpt_block(excerpts),
                allowed=", ".join(allowed_ids),
            ),
        },
    ]
