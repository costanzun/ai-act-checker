"""Strings and small helpers shared by the Markdown and PDF exporters."""

from __future__ import annotations

import re
from collections.abc import Iterator

from app.schemas import Assessment

TOKEN_RE = re.compile(r"\[\[([^\[\]\s]+)\]\]")
APPENDIX_CAP = 1500

TIER_LABELS = {
    "prohibited": {"en": "Prohibited practice", "it": "Pratica vietata"},
    "high_risk": {"en": "High-risk AI system", "it": "Sistema di IA ad alto rischio"},
    "limited_risk": {"en": "Transparency obligations", "it": "Obblighi di trasparenza"},
    "minimal_risk": {"en": "Minimal risk", "it": "Rischio minimo"},
    "out_of_scope": {"en": "Outside the scope of the Act", "it": "Fuori dall'ambito di applicazione"},
}
TIER_COLORS = {
    "prohibited": "#9F1239",
    "high_risk": "#B45309",
    "limited_risk": "#1D4ED8",
    "minimal_risk": "#15803D",
    "out_of_scope": "#64748B",
}

S: dict[str, dict[str, str]] = {
    "title": {"en": "EU AI Act assessment", "it": "Valutazione AI Act UE"},
    "law_as_of": {"en": "Law as of", "it": "Normativa aggiornata al"},
    "checked": {"en": "checked on", "it": "verificata il"},
    "generated_with": {"en": "Generated with", "it": "Generata con"},
    "disclaimer": {"en": "Disclaimer", "it": "Avvertenza"},
    "description": {"en": "Described system", "it": "Sistema descritto"},
    "result": {"en": "Result", "it": "Esito"},
    "tier": {"en": "Classification", "it": "Classificazione"},
    "confidence": {"en": "Confidence", "it": "Affidabilità"},
    "role": {"en": "Role", "it": "Ruolo"},
    "reasoning": {"en": "Reasoning", "it": "Motivazione"},
    "findings": {"en": "Findings", "it": "Riscontri"},
    "decisive": {"en": "decisive", "it": "determinante"},
    "citations": {"en": "Citations", "it": "Riferimenti"},
    "obligations": {"en": "Obligations", "it": "Obblighi"},
    "applies_from": {"en": "applies from", "it": "si applica dal"},
    "must": {"en": "mandatory", "it": "obbligatorio"},
    "should": {"en": "recommended", "it": "raccomandato"},
    "checklist": {"en": "Compliance checklist", "it": "Checklist di conformità"},
    "template": {"en": "Template hint", "it": "Indicazione per il modello"},
    "timeline": {"en": "Timeline", "it": "Scadenze"},
    "assumptions": {"en": "Assumptions and uncertainties", "it": "Ipotesi e incertezze"},
    "assumptions_sub": {"en": "Assumptions", "it": "Ipotesi"},
    "uncertainties_sub": {"en": "Uncertainties", "it": "Incertezze"},
    "unresolved": {"en": "Facts still unknown", "it": "Fatti ancora ignoti"},
    "related": {"en": "Related provisions", "it": "Disposizioni correlate"},
    "appendix": {"en": "Cited provisions", "it": "Disposizioni citate"},
    "full_text_truncated": {"en": "[text truncated, see EUR-Lex]", "it": "[testo troncato, vedi EUR-Lex]"},
    "eurlex": {"en": "Read on EUR-Lex", "it": "Leggi su EUR-Lex"},
    "footer": {"en": "Not legal advice", "it": "Non costituisce consulenza legale"},
    "generated": {"en": "generated", "it": "generato il"},
    "page": {"en": "Page", "it": "Pagina"},
    "none": {"en": "None.", "it": "Nessuno."},
}
ROLES = {
    "provider": {"en": "Provider", "it": "Fornitore"},
    "deployer": {"en": "Deployer", "it": "Deployer (utilizzatore)"},
    "both": {"en": "Provider and deployer", "it": "Fornitore e deployer"},
    "other": {"en": "Other (importer, distributor, ...)", "it": "Altro (importatore, distributore, ...)"},
    "unknown": {"en": "Not determined", "it": "Non determinato"},
}
OBLIGATION_ROLES = {
    "provider": ROLES["provider"],
    "deployer": {"en": "Deployer", "it": "Deployer"},
    "both": {"en": "Provider and deployer", "it": "Fornitore e deployer"},
}
CONFIDENCE = {
    "high": {"en": "High", "it": "Alta"},
    "medium": {"en": "Medium", "it": "Media"},
    "low": {"en": "Low", "it": "Bassa"},
}
CATEGORIES = {
    "governance": {"en": "Governance and risk management", "it": "Governance e gestione del rischio"},
    "documentation": {"en": "Documentation and records", "it": "Documentazione e registri"},
    "data": {"en": "Data", "it": "Dati"},
    "transparency": {"en": "Transparency", "it": "Trasparenza"},
    "oversight": {"en": "Human oversight", "it": "Sorveglianza umana"},
    "registration": {"en": "Registration", "it": "Registrazione"},
    "monitoring": {"en": "Monitoring", "it": "Monitoraggio"},
    "literacy": {"en": "AI literacy", "it": "Alfabetizzazione in materia di IA"},
    "other": {"en": "Other", "it": "Altro"},
}
MONTHS_IT = ["gennaio", "febbraio", "marzo", "aprile", "maggio", "giugno", "luglio", "agosto",
             "settembre", "ottobre", "novembre", "dicembre"]


def t(key: str, lang: str) -> str:
    return S[key][lang]


def pick(d: dict[str, str] | None, lang: str) -> str:
    """Bilingual dict -> text, falling back to the other language."""
    if not d:
        return ""
    return d.get(lang) or d.get("en") or next(iter(d.values()), "")


def fmt_date(iso: str | None, lang: str) -> str:
    """ISO date (or datetime) -> '3 November 2026' / '3 novembre 2026'."""
    if not iso:
        return ""
    m = re.match(r"(\d{4})-(\d{2})-(\d{2})", iso)
    if not m:
        return iso
    y, mo, d = int(m[1]), int(m[2]), int(m[3])
    if lang == "it":
        return f"{d} {MONTHS_IT[mo - 1]} {y}"
    en = ["January", "February", "March", "April", "May", "June", "July", "August",
          "September", "October", "November", "December"]
    return f"{d} {en[mo - 1]} {y}"


def segments(text: str) -> Iterator[tuple[str, str]]:
    """Split text into ('text', s) and ('cite', provision_id) parts."""
    pos = 0
    for m in TOKEN_RE.finditer(text):
        if m.start() > pos:
            yield "text", text[pos : m.start()]
        yield "cite", m.group(1)
        pos = m.end()
    if pos < len(text):
        yield "text", text[pos:]


def _tokens(text: str) -> list[str]:
    return TOKEN_RE.findall(text or "")


def cited_ids(a: Assessment) -> list[str]:
    """Every distinct provision ID cited anywhere in the assessment, in first-use order."""
    seen: dict[str, None] = {}

    def add(ids) -> None:
        for i in ids:
            seen.setdefault(i, None)

    c = a.classification
    add(_tokens(a.reasoning_md))
    for f in c.findings:
        add(f.citations)
        add(_tokens(f.rationale.get(a.language, "")))
    for ids in c.overlays.values():
        add(ids)
    for o in a.obligations:
        add(o.citations)
        add(_tokens(o.summary.get(a.language, "")))
    for ci in a.checklist:
        add(ci.citations)
        add(_tokens(ci.description.get(a.language, "")))
    for m in c.applies_from:
        add(m.citations)
    for r in a.related_provisions:
        add([r.id])
    return list(seen)


def linkify_md(text: str, store, lang: str) -> str:
    """Replace [[id]] tokens by Markdown links; unknown IDs become plain labels."""
    out = []
    for kind, val in segments(text):
        if kind == "text":
            out.append(val)
        elif store.exists(val):
            out.append(f"[{store.label(val, lang)}]({store.eurlex_url(val, lang)})")
        else:
            out.append(store.label(val, lang))
    return "".join(out)


def appendix_text(store, pid: str, lang: str) -> tuple[str, bool]:
    """Full text of a provision, capped; returns (text, truncated)."""
    txt = store.full_text(pid, lang).strip()
    if len(txt) <= APPENDIX_CAP:
        return txt, False
    cut = txt[:APPENDIX_CAP].rsplit(" ", 1)[0].rstrip()
    return cut + " ...", True
