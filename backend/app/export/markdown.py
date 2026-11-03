"""Markdown export of an Assessment."""

from __future__ import annotations

from datetime import datetime, timezone

from app.corpus.store import CorpusStore
from app.export.i18n import (
    CATEGORIES, CONFIDENCE, OBLIGATION_ROLES, ROLES, TIER_LABELS, appendix_text, cited_ids, fmt_date,
    linkify_md, pick, t,
)
from app.schemas import Assessment


def render_markdown(a: Assessment, store: CorpusStore, now: datetime | None = None) -> str:
    lang = a.language
    c = a.classification
    lk = lambda s: linkify_md(s, store, lang)  # noqa: E731
    lab = lambda i: store.label(i, lang)  # noqa: E731

    def cites(ids: list[str]) -> str:
        return ", ".join(f"[{lab(i)}]({store.eurlex_url(i, lang)})" if store.exists(i) else lab(i) for i in ids)

    now = now or datetime.now(timezone.utc)
    L: list[str] = []
    L += [f"# {t('title', lang)}", ""]
    L += [
        f"*{t('law_as_of', lang)} {fmt_date(a.law_as_of, lang)} ({t('checked', lang)} {fmt_date(a.checked_at, lang)}). "
        f"{t('generated_with', lang)} {a.model.provider} / {a.model.model}.*",
        "",
    ]
    L += [f"> **{t('disclaimer', lang)}.** {pick(a.disclaimer, lang)}", ""]

    L += [f"## {t('description', lang)}", ""]
    L += [f"> {line}" if line.strip() else ">" for line in a.description.strip().splitlines()]
    L += [""]

    L += [f"## {t('result', lang)}", ""]
    L += [
        f"- **{t('tier', lang)}:** {TIER_LABELS[c.tier][lang]}",
        f"- **{t('confidence', lang)}:** {CONFIDENCE[c.confidence][lang]}",
        f"- **{t('role', lang)}:** {ROLES[c.role][lang]}",
        "",
    ]
    L += [f"## {t('reasoning', lang)}", "", lk(a.reasoning_md.strip()), ""]

    if c.findings:
        L += [f"## {t('findings', lang)}", ""]
        for f in c.findings:
            dec = f" ({t('decisive', lang)})" if f.decisive else ""
            L += [f"### {pick(f.title, lang)}{dec}", "", lk(pick(f.rationale, lang)), ""]
            if f.citations:
                L += [f"**{t('citations', lang)}:** {cites(f.citations)}", ""]

    if a.obligations:
        L += [f"## {t('obligations', lang)}", ""]
        by_cat: dict[str, list] = {}
        for o in a.obligations:
            by_cat.setdefault(o.category, []).append(o)
        for cat in CATEGORIES:
            if cat not in by_cat:
                continue
            L += [f"### {CATEGORIES[cat][lang]}", ""]
            for o in by_cat[cat]:
                meta = [OBLIGATION_ROLES[o.role][lang], t(o.priority, lang)]
                if o.applies_from:
                    meta.append(f"{t('applies_from', lang)} {fmt_date(o.applies_from, lang)}")
                L += [f"- **{pick(o.title, lang)}** ({'; '.join(meta)}). {lk(pick(o.summary, lang))}"]
                if o.citations:
                    L += [f"  - {cites(o.citations)}"]
            L += [""]

    if a.checklist:
        L += [f"## {t('checklist', lang)}", ""]
        for ci in a.checklist:
            L += [f"- [ ] **{pick(ci.title, lang)}**. {lk(pick(ci.description, lang))}"]
            if ci.citations:
                L += [f"  - {cites(ci.citations)}"]
            if ci.template_hint:
                L += [f"  - *{t('template', lang)}:* {pick(ci.template_hint, lang)}"]
        L += [""]

    if c.applies_from:
        L += [f"## {t('timeline', lang)}", ""]
        for m in sorted(c.applies_from, key=lambda m: m.date):
            extra = f" ({cites(m.citations)})" if m.citations else ""
            L += [f"- **{fmt_date(m.date, lang)}**: {pick(m.what, lang)}{extra}"]
        L += [""]

    if c.assumptions or a.uncertainties or c.unresolved:
        L += [f"## {t('assumptions', lang)}", ""]
        if c.assumptions:
            L += [f"### {t('assumptions_sub', lang)}", ""] + [f"- {pick(x, lang)}" for x in c.assumptions] + [""]
        if a.uncertainties:
            L += [f"### {t('uncertainties_sub', lang)}", ""] + [f"- {pick(x, lang)}" for x in a.uncertainties] + [""]
        if c.unresolved:
            L += [f"### {t('unresolved', lang)}", ""] + [f"- `{p}`" for p in c.unresolved] + [""]

    if a.related_provisions:
        L += [f"## {t('related', lang)}", ""]
        for r in a.related_provisions:
            L += [f"- {cites([r.id])}: {pick(r.why, lang)}"]
        L += [""]

    ids = [i for i in cited_ids(a) if store.exists(i)]
    if ids:
        L += [f"## {t('appendix', lang)}", ""]
        for i in ids:
            txt, trunc = appendix_text(store, i, lang)
            L += [f"### {lab(i)}", ""]
            L += [f"> {line}" if line.strip() else ">" for line in txt.splitlines()]
            if trunc:
                L += [">", f"> {t('full_text_truncated', lang)}"]
            L += ["", f"[{t('eurlex', lang)}]({store.eurlex_url(i, lang)})", ""]

    L += ["---", "", f"*{t('footer', lang)} · {t('generated', lang)} {fmt_date(now.date().isoformat(), lang)} · "
          f"{t('law_as_of', lang).lower()} {fmt_date(a.law_as_of, lang)}*", ""]
    return "\n".join(L)
