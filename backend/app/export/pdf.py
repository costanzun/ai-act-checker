"""PDF export of an Assessment (fpdf2, pure Python, bundled DejaVu Sans)."""

from __future__ import annotations

import re
from datetime import datetime, timezone
from pathlib import Path

from fpdf import FPDF
from fpdf.enums import XPos, YPos

from app.corpus.store import CorpusStore
from app.export.i18n import (
    CATEGORIES, CONFIDENCE, OBLIGATION_ROLES, ROLES, TIER_COLORS, TIER_LABELS, appendix_text, cited_ids,
    fmt_date, pick, segments, t, what_if_lines,
)
from app.schemas import Assessment

FONT_DIR = Path(__file__).parent / "fonts"
BODY = 10.5
INK = (30, 41, 59)
MUTED = (100, 116, 139)
LINK = (29, 78, 216)
RULE = (203, 213, 225)
_BOLD_RE = re.compile(r"\*\*(.+?)\*\*")


def _rgb(hex_: str) -> tuple[int, int, int]:
    h = hex_.lstrip("#")
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


class _Doc(FPDF):
    def __init__(self, lang: str, law_as_of: str, today: str) -> None:
        super().__init__(orientation="P", unit="mm", format="A4")
        self.lang, self.law_as_of, self.today = lang, law_as_of, today
        self.set_margins(18, 18, 18)
        self.set_auto_page_break(True, margin=20)
        self.add_font("DejaVu", "", str(FONT_DIR / "DejaVuSans.ttf"))
        self.add_font("DejaVu", "B", str(FONT_DIR / "DejaVuSans-Bold.ttf"))
        self.add_font("DejaVu", "I", str(FONT_DIR / "DejaVuSans-Oblique.ttf"))
        self.set_text_color(*INK)
        self.alias_nb_pages()

    def footer(self) -> None:
        self.set_y(-14)
        self.set_draw_color(*RULE)
        self.line(self.l_margin, self.get_y(), self.w - self.r_margin, self.get_y())
        self.set_font("DejaVu", "", 7.5)
        self.set_text_color(*MUTED)
        left = (f"{t('footer', self.lang)} · {t('generated', self.lang)} {self.today} · "
                f"{t('law_as_of', self.lang).lower()} {self.law_as_of}")
        self.set_y(-12)
        self.cell(0, 5, left, align="L")
        self.set_x(self.l_margin)
        self.cell(0, 5, f"{t('page', self.lang)} {self.page_no()} / {{nb}}", align="R")
        self.set_text_color(*INK)

    # -- helpers ------------------------------------------------------------ #
    def nl(self, h: float = 0) -> None:
        self.ln(h)
        self.set_x(self.l_margin)

    def heading(self, text: str, level: int = 1, color=INK) -> None:
        size = {1: 14, 2: 11.5, 3: 10.5}[level]
        self.nl(4 if level == 1 else 2.5)
        if self.get_y() > self.h - 45:
            self.add_page()
        self.set_font("DejaVu", "B", size)
        self.set_text_color(*color)
        self.multi_cell(0, size * 0.5 + 2, text, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        if level == 1:
            self.set_draw_color(*RULE)
            self.line(self.l_margin, self.get_y(), self.w - self.r_margin, self.get_y())
            self.ln(2)
        self.set_text_color(*INK)

    def rich(self, text: str, store: CorpusStore, size: float = BODY, style: str = "", color=INK, lh: float = 5.2) -> None:
        """Write inline text: [[id]] -> underlined EUR-Lex link, **bold** -> bold."""
        for kind, val in segments(text):
            if kind == "cite":
                label = store.label(val, self.lang)
                if store.exists(val):
                    self.set_text_color(*LINK)
                    self.set_font_style_u(size, style)
                    self.write(lh, label, link=store.eurlex_url(val, self.lang))
                else:
                    self.write(lh, label)
                self.set_text_color(*color)
                continue
            for i, part in enumerate(_BOLD_RE.split(val)):
                if not part:
                    continue
                b = i % 2 == 1
                st = ("B" if b else "") + ("I" if "I" in style and not b else "")
                if "B" in style:
                    st = "B"
                self.set_font("DejaVu", st, size)
                self.set_text_color(*color)
                self.write(lh, part)
        self.set_text_color(*INK)

    def set_font_style_u(self, size: float, style: str) -> None:
        self.set_font("DejaVu", ("B" if "B" in style else "") + "U", size)

    def para(self, text: str, store: CorpusStore, **kw) -> None:
        self.set_x(self.l_margin)
        self.rich(text, store, **kw)
        self.ln(kw.get("lh", 5.2) + 1.2)
        self.set_x(self.l_margin)

    def cite_line(self, ids: list[str], store: CorpusStore, prefix: str = "", size: float = 9.5) -> None:
        self.set_x(self.l_margin)
        self.set_font("DejaVu", "", size)
        self.set_text_color(*MUTED)
        if prefix:
            self.write(4.8, prefix + " ")
        for n, i in enumerate(ids):
            if n:
                self.set_font("DejaVu", "", size)
                self.set_text_color(*MUTED)
                self.write(4.8, ", ")
            self.rich(f"[[{i}]]", store, size=size, lh=4.8)
        self.ln(5.6)
        self.set_x(self.l_margin)
        self.set_text_color(*INK)

    def block_markdown(self, md: str, store: CorpusStore) -> None:
        for raw in md.splitlines():
            line = raw.rstrip()
            if not line.strip():
                self.ln(1.5)
                continue
            m = re.match(r"^(#{1,6})\s+(.*)", line)
            if m:
                self.heading(m.group(2), 3 if len(m.group(1)) > 2 else 2)
                continue
            b = re.match(r"^\s*(?:[-*]|\d+\.)\s+(.*)", line)
            self.set_x(self.l_margin)
            if b:
                self.set_font("DejaVu", "", BODY)
                self.set_x(self.l_margin + 3)
                self.write(5.2, "•  ")
                self.set_left_margin(self.l_margin + 8)
                self.set_x(self.l_margin)
                self.rich(b.group(1), store)
                self.set_left_margin(self.l_margin - 8)
                self.ln(6.4)
            else:
                self.rich(line.strip(), store)
                self.ln(6.4)
            self.set_x(self.l_margin)


def render_pdf(a: Assessment, store: CorpusStore, now: datetime | None = None) -> bytes:
    lang = a.language
    c = a.classification
    now = now or datetime.now(timezone.utc)
    pdf = _Doc(lang, a.law_as_of, fmt_date(now.date().isoformat(), lang))
    pdf.set_title(f"{t('title', lang)} - {TIER_LABELS[c.tier][lang]}")
    pdf.set_author("EU AI Act Checker")
    pdf.set_creator("EU AI Act Checker")
    pdf.add_page()

    # header band
    color = _rgb(TIER_COLORS[c.tier])
    pdf.set_fill_color(*color)
    pdf.rect(0, 0, pdf.w, 34, style="F")
    pdf.set_xy(18, 8)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("DejaVu", "B", 19)
    pdf.cell(0, 9, t("title", lang), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_x(18)
    pdf.set_font("DejaVu", "", 12)
    pdf.cell(0, 8, TIER_LABELS[c.tier][lang], new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_x(18)
    pdf.set_font("DejaVu", "", 8.5)
    pdf.cell(0, 5, f"{t('law_as_of', lang)} {fmt_date(a.law_as_of, lang)} ({t('checked', lang)} "
                   f"{fmt_date(a.checked_at, lang)}) · {a.model.provider} / {a.model.model}")
    pdf.set_text_color(*INK)
    pdf.set_y(40)

    # disclaimer callout
    pdf.set_fill_color(241, 245, 249)
    pdf.set_draw_color(*color)
    pdf.set_font("DejaVu", "", 8.5)
    pdf.set_text_color(71, 85, 105)
    y0 = pdf.get_y()
    pdf.set_x(22)
    pdf.multi_cell(pdf.w - 18 - 22, 4.4, f"{t('disclaimer', lang)}. {pick(a.disclaimer, lang)}", fill=True,
                   new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_line_width(0.8)
    pdf.line(19, y0, 19, pdf.get_y())
    pdf.set_line_width(0.2)
    pdf.set_text_color(*INK)

    # description
    pdf.heading(t("description", lang))
    pdf.set_left_margin(23)
    pdf.set_x(23)
    pdf.set_font("DejaVu", "I", BODY)
    pdf.set_text_color(*MUTED)
    pdf.multi_cell(0, 5.2, f"“{a.description.strip()}”", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_left_margin(18)
    pdf.set_x(18)
    pdf.set_text_color(*INK)

    # result
    pdf.heading(t("result", lang))
    for label, val in [(t("tier", lang), TIER_LABELS[c.tier][lang]), (t("confidence", lang), CONFIDENCE[c.confidence][lang]),
                       (t("role", lang), ROLES[c.role][lang])]:
        pdf.set_x(18)
        pdf.set_font("DejaVu", "B", BODY)
        pdf.cell(38, 6, label)
        pdf.set_font("DejaVu", "", BODY)
        if label == t("tier", lang):
            pdf.set_text_color(*color)
            pdf.set_font("DejaVu", "B", BODY)
        pdf.cell(0, 6, val, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.set_text_color(*INK)

    pdf.heading(t("reasoning", lang))
    pdf.block_markdown(a.reasoning_md.strip(), store)

    if c.findings:
        pdf.heading(t("findings", lang))
        for f in c.findings:
            dec = f"  ({t('decisive', lang)})" if f.decisive else ""
            pdf.heading(pick(f.title, lang) + dec, 2)
            pdf.para(pick(f.rationale, lang), store)
            if f.citations:
                pdf.cite_line(f.citations, store, t("citations", lang) + ":")

    if a.obligations:
        pdf.heading(t("obligations", lang))
        by_cat: dict[str, list] = {}
        for o in a.obligations:
            by_cat.setdefault(o.category, []).append(o)
        for cat in CATEGORIES:
            if cat not in by_cat:
                continue
            pdf.heading(CATEGORIES[cat][lang], 2)
            for o in by_cat[cat]:
                meta = [OBLIGATION_ROLES[o.role][lang], t(o.priority, lang)]
                if o.applies_from:
                    meta.append(f"{t('applies_from', lang)} {fmt_date(o.applies_from, lang)}")
                pdf.set_x(18)
                pdf.set_font("DejaVu", "B", BODY)
                pdf.multi_cell(0, 5.2, pick(o.title, lang), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
                pdf.set_font("DejaVu", "", 8.5)
                pdf.set_text_color(*MUTED)
                pdf.multi_cell(0, 4.4, " · ".join(meta), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
                pdf.set_text_color(*INK)
                pdf.para(pick(o.summary, lang), store)
                if o.citations:
                    pdf.cite_line(o.citations, store)

    if a.checklist:
        pdf.heading(t("checklist", lang))
        for ci in a.checklist:
            pdf.set_x(18)
            pdf.set_font("DejaVu", "", 13)
            pdf.cell(8, 6, "☐")
            pdf.set_left_margin(26)
            pdf.set_x(26)
            pdf.set_font("DejaVu", "B", BODY)
            pdf.multi_cell(0, 5.6, pick(ci.title, lang), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            pdf.para(pick(ci.description, lang), store)
            if ci.citations:
                pdf.cite_line(ci.citations, store)
            if ci.template_hint:
                pdf.set_font("DejaVu", "I", 9)
                pdf.set_text_color(*MUTED)
                pdf.multi_cell(0, 4.6, f"{t('template', lang)}: {pick(ci.template_hint, lang)}",
                               new_x=XPos.LMARGIN, new_y=YPos.NEXT)
                pdf.set_text_color(*INK)
                pdf.ln(1)
            pdf.set_left_margin(18)
            pdf.set_x(18)
            pdf.ln(1.5)

    if c.applies_from:
        pdf.heading(t("timeline", lang))
        for m in sorted(c.applies_from, key=lambda m: m.date):
            pdf.set_x(18)
            pdf.set_font("DejaVu", "B", BODY)
            pdf.cell(42, 5.6, fmt_date(m.date, lang))
            pdf.set_left_margin(60)
            pdf.set_x(60)
            pdf.rich(pick(m.what, lang), store)
            pdf.ln(5.6)
            if m.citations:
                pdf.cite_line(m.citations, store, size=9)
            pdf.set_left_margin(18)
            pdf.set_x(18)
            pdf.ln(1.5)

    if c.assumptions or a.uncertainties or c.unresolved or a.what_if:
        pdf.heading(t("assumptions", lang))
        for title, items in [(t("what_if", lang), what_if_lines(a, lang)),
                             (t("assumptions_sub", lang), [pick(x, lang) for x in c.assumptions]),
                             (t("uncertainties_sub", lang), [pick(x, lang) for x in a.uncertainties]),
                             (t("unresolved", lang), list(c.unresolved))]:
            if not items:
                continue
            pdf.heading(title, 2)
            for it in items:
                pdf.set_x(18)
                pdf.set_font("DejaVu", "", BODY)
                pdf.cell(6, 5.2, "•")
                pdf.set_x(24)
                pdf.multi_cell(0, 5.2, it, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
                pdf.ln(1)

    if a.related_provisions:
        pdf.heading(t("related", lang))
        for r in a.related_provisions:
            pdf.set_x(18)
            pdf.rich(f"[[{r.id}]]: ", store, style="B")
            pdf.rich(pick(r.why, lang), store)
            pdf.ln(7)

    ids = [i for i in cited_ids(a) if store.exists(i)]
    if ids:
        pdf.add_page()
        pdf.heading(t("appendix", lang))
        for i in ids:
            pdf.heading(store.label(i, lang), 2)
            txt, trunc = appendix_text(store, i, lang)
            pdf.set_x(18)
            pdf.set_font("DejaVu", "", 9)
            pdf.set_text_color(51, 65, 85)
            pdf.multi_cell(0, 4.5, txt + (f"\n{t('full_text_truncated', lang)}" if trunc else ""),
                           new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            pdf.set_x(18)
            pdf.set_font("DejaVu", "U", 8.5)
            pdf.set_text_color(*LINK)
            pdf.cell(0, 5, t("eurlex", lang), link=store.eurlex_url(i, lang), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            pdf.set_text_color(*INK)

    return bytes(pdf.output())
