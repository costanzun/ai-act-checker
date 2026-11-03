"""Application timeline of the AI Act as consolidated on 27 July 2026.

Source: Art. 113 (as replaced/supplemented by Regulation (EU) 2026/1744) and the
transitional rules in Art. 111. Every date below is taken from the text.
"""

from __future__ import annotations

from datetime import date

from .models import Milestone

# Key dates (ISO) — Art. 113 consolidated, Art. 111.
ENTRY_INTO_FORCE = "2024-08-01"  # Art. 113 first para: 20th day after OJ publication (12.7.2024)
PROHIBITIONS = "2025-02-02"  # Art. 113(a): Chapters I and II
NEW_PROHIBITIONS = "2026-12-02"  # Art. 113(a): Art. 5(1)(ba), (bb), 5(1a), 5(1b)
GPAI_AND_GOVERNANCE = "2025-08-02"  # Art. 113(b): Ch. III Sec. 4, Ch. V, VII, XII, Art. 78
OMNIBUS_IN_FORCE = "2026-07-27"  # Art. 113(d): Arts 102-110; Reg. 2026/1744 in force
GENERAL = "2026-08-02"  # Art. 113 second para (incl. Art. 50)
ART50_2_LEGACY = "2026-12-02"  # Art. 111(4)
GPAI_LEGACY = "2027-08-02"  # Art. 111(3)
HIGH_RISK_ANNEX_III = "2027-12-02"  # Art. 113(c)(i)
HIGH_RISK_ANNEX_I = "2028-08-02"  # Art. 113(c)(ii)
PUBLIC_AUTHORITY_LEGACY = "2030-08-02"  # Art. 111(2) second sentence
LARGE_SCALE_IT_LEGACY = "2030-12-31"  # Art. 111(1)

_MILESTONES: list[tuple[str, str, dict[str, str], list[str]]] = [
    (
        "entry-into-force",
        ENTRY_INTO_FORCE,
        {
            "en": "The AI Act enters into force (20th day after publication in the Official Journal).",
            "it": "Il regolamento sull'IA entra in vigore (ventesimo giorno successivo alla pubblicazione nella Gazzetta ufficiale).",
        },
        ["art:113"],
    ),
    (
        "chapters-i-ii",
        PROHIBITIONS,
        {
            "en": "General provisions (incl. AI literacy, Art. 4) and the prohibited practices of Art. 5 apply.",
            "it": "Si applicano le disposizioni generali (compresa l'alfabetizzazione in materia di IA, art. 4) e i divieti dell'art. 5.",
        },
        ["art:113", "art:4", "art:5"],
    ),
    (
        "gpai-governance-penalties",
        GPAI_AND_GOVERNANCE,
        {
            "en": "Obligations for general-purpose AI models, notified bodies, governance and penalties apply.",
            "it": "Si applicano gli obblighi per i modelli di IA per finalità generali, le norme sugli organismi notificati, la governance e le sanzioni.",
        },
        ["art:113", "art:53", "art:99"],
    ),
    (
        "omnibus-in-force",
        OMNIBUS_IN_FORCE,
        {
            "en": "Regulation (EU) 2026/1744 (Digital Omnibus on AI) enters into force; Articles 102 to 110 (amendments to sectoral product legislation) apply.",
            "it": "Entra in vigore il regolamento (UE) 2026/1744 (Omnibus digitale sull'IA); si applicano gli articoli da 102 a 110 (modifiche alla normativa settoriale sui prodotti).",
        },
        ["art:113"],
    ),
    (
        "general-application",
        GENERAL,
        {
            "en": "General date of application, including the transparency obligations of Art. 50.",
            "it": "Data generale di applicazione, compresi gli obblighi di trasparenza dell'art. 50.",
        },
        ["art:113", "art:50"],
    ),
    (
        "new-prohibitions-and-marking-legacy",
        NEW_PROHIBITIONS,
        {
            "en": "New prohibitions on AI-generated non-consensual intimate material and child sexual abuse material apply (Art. 5(1)(ba), (bb), 5(1a), 5(1b)); generative AI systems placed on the market before 2 August 2026 must comply with the marking duty of Art. 50(2).",
            "it": "Si applicano i nuovi divieti relativi a materiale intimo non consensuale e materiale pedopornografico generati dall'IA (art. 5, par. 1, lett. ba) e bb), par. 1 bis e 1 ter); i sistemi generativi immessi sul mercato prima del 2 agosto 2026 devono rispettare l'obbligo di marcatura dell'art. 50, par. 2.",
        },
        ["art:113", "art:5.1.ba", "art:5.1.bb", "art:5.1a", "art:5.1b", "art:111.4"],
    ),
    (
        "gpai-legacy",
        GPAI_LEGACY,
        {
            "en": "Providers of general-purpose AI models placed on the market before 2 August 2025 must comply.",
            "it": "I fornitori di modelli di IA per finalità generali immessi sul mercato prima del 2 agosto 2025 devono conformarsi.",
        },
        ["art:111.3"],
    ),
    (
        "high-risk-annex-iii",
        HIGH_RISK_ANNEX_III,
        {
            "en": "High-risk rules (Chapter III, Sections 1–3) apply to AI systems classified as high-risk under Art. 6(2) and Annex III.",
            "it": "Le norme sui sistemi ad alto rischio (capo III, sezioni 1-3) si applicano ai sistemi classificati ad alto rischio ai sensi dell'art. 6, par. 2, e dell'allegato III.",
        },
        ["art:113", "art:6.2", "annex:III"],
    ),
    (
        "high-risk-annex-i",
        HIGH_RISK_ANNEX_I,
        {
            "en": "High-risk rules (Chapter III, Sections 1–3) apply to AI systems classified as high-risk under Art. 6(1) and Annex I.",
            "it": "Le norme sui sistemi ad alto rischio (capo III, sezioni 1-3) si applicano ai sistemi classificati ad alto rischio ai sensi dell'art. 6, par. 1, e dell'allegato I.",
        },
        ["art:113", "art:6.1", "annex:I"],
    ),
    (
        "public-authority-legacy",
        PUBLIC_AUTHORITY_LEGACY,
        {
            "en": "Providers and deployers of legacy high-risk AI systems intended for use by public authorities must comply.",
            "it": "Fornitori e deployer di sistemi ad alto rischio preesistenti destinati a essere usati da autorità pubbliche devono conformarsi.",
        },
        ["art:111.2"],
    ),
    (
        "large-scale-it-legacy",
        LARGE_SCALE_IT_LEGACY,
        {
            "en": "AI components of EU large-scale IT systems (Annex X) placed on the market before 2 August 2027 must comply.",
            "it": "I componenti di IA dei sistemi IT su larga scala dell'UE (allegato X) immessi sul mercato prima del 2 agosto 2027 devono conformarsi.",
        },
        ["art:111.1", "annex:X"],
    ),
]


def _status(d: str, today: date) -> str:
    return "in_force" if date.fromisoformat(d) <= today else "upcoming"


def timeline(today: date | None = None) -> list[Milestone]:
    """All milestones from Art. 113/111 with status relative to ``today``."""
    today = today or date.today()
    return [
        Milestone(id=mid, date=d, what=dict(what), citations=list(cites), status=_status(d, today))
        for mid, d, what, cites in _MILESTONES
    ]


def milestones_by_id(ids: list[str], today: date | None = None) -> list[Milestone]:
    by_id = {m.id: m for m in timeline(today)}
    return [by_id[i] for i in ids if i in by_id]


def timeline_citation_ids() -> set[str]:
    return {c for _, _, _, cites in _MILESTONES for c in cites}
