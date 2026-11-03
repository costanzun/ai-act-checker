"""Parser for the consolidated EU AI Act (Cellar XHTML) into the corpus JSON.

Inputs (never executed, only parsed):

* the consolidated regulation ``02024R1689-20260727`` (articles, annexes,
  amendment markers ``▼M1`` / ``▼B``);
* the original Official Journal text of Regulation (EU) 2024/1689 (``32024R1689``),
  used **only** for the 180 recitals, because EUR-Lex consolidations omit the
  preamble.

No network access happens here. See ``scripts/build_corpus.py`` for the CLI.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from lxml import etree

CELEX = "02024R1689-20260727"
SOURCE_URL = "http://publications.europa.eu/resource/celex/02024R1689-20260727"
ELI_URL = "https://eur-lex.europa.eu/eli/reg/2024/1689/2026-07-27"
AMENDING_ACTS: list[dict[str, str]] = [
    {
        "celex": "32026R1744",
        "marker": "M1",
        "short_title": "Regulation (EU) 2026/1744 (Digital Omnibus on AI)",
        "oj_date": "2026-07-24",
        "in_force": "2026-07-27",
    }
]

# --------------------------------------------------------------------------- #
# Text helpers
# --------------------------------------------------------------------------- #

_SUPER = str.maketrans("0123456789+-", "⁰¹²³⁴⁵⁶⁷⁸⁹⁺⁻")
_MARKER_RE = re.compile(r"[▼►◄]\s*(?:[MBC]\d*)?")
_WS_RE = re.compile(r"[\s   ​]+")
_EMPTY_PAREN_RE = re.compile(r"\(\s*\)")
_SPACE_BEFORE_PUNCT_RE = re.compile(r"\s+([;:,.])")
_INLINE_TAGS = {"a", "span", "i", "b", "em", "strong", "sup", "sub", "u", "br", "small"}
_ORDINAL_SUFFIX = {
    "bis": "a",
    "ter": "b",
    "quater": "c",
    "quinquies": "d",
    "sexies": "e",
    "septies": "f",
    "octies": "g",
    "novies": "h",
    "decies": "i",
}
_LABEL_RE = re.compile(r"^\s*(\d+(?:\.\d+)*\.|\([a-z]{1,4}\)|\(\d+\))\s+")


def _ln(el: etree._Element) -> str:
    """Local tag name (namespace stripped); ``''`` for comments/PIs."""
    return etree.QName(el).localname if isinstance(el.tag, str) else ""


def _cls(el: etree._Element) -> str:
    return el.get("class") or ""


def _norm(s: str) -> str:
    """Normalise whitespace, drop amendment glyphs and footnote artefacts."""
    s = _MARKER_RE.sub("", s)
    s = _EMPTY_PAREN_RE.sub("", s)
    s = _WS_RE.sub(" ", s).strip()
    return _SPACE_BEFORE_PUNCT_RE.sub(r"\1", s)


def _is_footnote_ref(el: etree._Element) -> bool:
    """True for ``<a href="#E0001"><span class="superscript">1</span></a>`` style refs."""
    if _ln(el) != "a":
        return False
    href = el.get("href") or ""
    if not href.startswith("#"):
        return False
    return any(
        _ln(c) == "span" and ("super" in _cls(c)) for c in el.iter() if c is not el
    ) or (el.get("id") or "").startswith("src.")


def _walk_text(n: etree._Element, out: list[str]) -> None:
    """Append the text of ``n`` (without its tail) to ``out``, dropping footnote refs."""
    tag = _ln(n)
    if not tag:
        return
    c = _cls(n)
    if _is_footnote_ref(n) or "no-parag" in c:
        return
    if tag == "br":
        out.append(" ")
        return
    if tag == "sup" or (tag == "span" and "super" in c):
        inner = "".join(n.itertext())
        out.append(inner.translate(_SUPER) if inner.strip().isdigit() else inner)
        return
    if n.text:
        out.append(n.text)
    for ch in n:
        _walk_text(ch, out)
        if ch.tail:
            out.append(ch.tail)


def _raw_text(el: etree._Element, *, with_tail: bool = False) -> str:
    """Concatenate the (un-normalised) text of ``el``; optionally include its tail."""
    out: list[str] = []
    _walk_text(el, out)
    if with_tail and el.tail:
        out.append(el.tail)
    return "".join(out)


def text_of(el: etree._Element) -> str:
    """Clean text of an element."""
    return _norm(_raw_text(el))


def _table_text(tbl: etree._Element) -> str:
    rows: list[str] = []
    for tr in tbl.iter("{*}tr"):
        cells = [text_of(td) for td in tr if _ln(td) in ("td", "th")]
        line = " ".join(c for c in cells if c)
        if line:
            rows.append(line)
    return "\n".join(rows)


def sentence_case(s: str) -> str:
    """Convert an ALL-CAPS heading to sentence case, keeping common acronyms."""
    s = _norm(s)
    if not s or s != s.upper():
        return s
    low = s.lower()
    low = low[0].upper() + low[1:]
    fixes = {"ai": "AI", "eu": "EU", "ia": "IA", "ue": "UE", "union": "Union", "unione": "Unione"}
    return re.sub(r"\b(ai|eu|ia|ue|union|unione)\b", lambda m: fixes[m.group(1)], low)


def token_of(raw: str) -> str | None:
    """Normalise a printed label such as ``(ba) ``, ``1a.``, ``1 bis.`` to an ID token."""
    s = _norm(raw).lstrip("‘’'\"“”«»„").strip()
    s = s.replace("(", "").replace(")", "").rstrip(".").strip().lower()
    m = re.fullmatch(r"([a-z0-9]+?)\s*(" + "|".join(_ORDINAL_SUFFIX) + ")", s)
    if m and (m.group(1).isdigit() or " " in s):
        s = m.group(1) + _ORDINAL_SUFFIX[m.group(2)]
    if re.fullmatch(r"[a-z0-9]+(\.[0-9]+)*", s):
        return s
    return None


def _is_alpha(tok: str) -> bool:
    return bool(re.fullmatch(r"[a-z]+", tok))


# --------------------------------------------------------------------------- #
# Intermediate event model
# --------------------------------------------------------------------------- #


@dataclass
class Amend:
    """Parsed amendment marker."""

    marker: str
    kind: str
    by: str

    def as_dict(self) -> dict[str, str]:
        return {"marker": self.marker, "kind": self.kind, "by": self.by}


@dataclass
class Text:
    """A run of unnumbered text."""

    s: str


@dataclass
class Del:
    """A ``▼M1 —————`` deletion marker."""

    amend: Amend


@dataclass
class Head:
    """A sub-heading inside an annex."""

    level: int
    s: str


@dataclass
class Item:
    """A numbered/lettered item together with its own (eagerly scanned) content."""

    raw: str
    token: str | None
    src: str  # "parag" | "grid" | "plain"
    amend: Amend | None
    events: list[Any] = field(default_factory=list)


@dataclass
class Node:
    """Mutable provision under construction."""

    id: str
    type: str
    segs: list[tuple[str, str]]
    parent: Node | None
    amend: Amend | None
    src: str = ""
    text_parts: list[str] = field(default_factory=list)
    body_parts: list[str] = field(default_factory=list)
    tail_parts: list[str] = field(default_factory=list)
    children: list[Node] = field(default_factory=list)
    plain: bool = False
    order: int = 0
    ctx: dict[str, Any] = field(default_factory=dict)
    heading_level: int = 0
    seen: set[str] = field(default_factory=set)  # child tokens used in the current sub-paragraph
    group: int = 1  # sub-paragraph counter when a child list restarts (e.g. Art. 43(1))


# --------------------------------------------------------------------------- #
# Labels
# --------------------------------------------------------------------------- #


def make_label(segs: list[tuple[str, str]], lang: str) -> str:
    """Build the display label for a provision from its path segments."""
    it = lang == "it"
    kind0, tok0 = segs[0]
    if kind0 == "rec":
        return f"{'Considerando' if it else 'Recital'} {tok0}"
    if kind0 == "art":
        s = f"Art. {tok0}"
        par = [t for k, t in segs if k == "par"]
        pts = [t for k, t in segs if k == "pt"]
        if par:
            s += f", par. {par[0]}" if it else f"({par[0]})"
        for i, p in enumerate(pts):
            if it:
                prev = pts[i - 1] if i else None
                lett = _is_alpha(p) and (prev is None or not _is_alpha(prev))
                s += f", lett. {p})" if lett else f", punto {p})"
            else:
                s += f", point ({p})" if (i == 0 and not par) else f"({p})"
        return s
    # annex
    s = f"{'Allegato' if it else 'Annex'} {tok0}"
    prev: str | None = None
    first = True
    rest = segs[1:]
    rest = [
        x for i, x in enumerate(rest)
        if not (x[0] == "apt" and i + 1 < len(rest) and rest[i + 1][1].startswith(x[1] + "."))
    ]
    for kind, tok in rest:
        if kind == "sec":
            s += f", {'sezione' if it else 'Section'} {tok.upper() if len(tok) == 1 else tok}"
            prev = None
            first = True
            continue
        if it:
            lett = _is_alpha(tok) and (prev is None or not _is_alpha(prev))
            s += f", lett. {tok})" if lett else f", punto {tok}" if not _is_alpha(tok) else f", punto {tok})"
        elif first:
            s += f", point {tok}" if not _is_alpha(tok) else f", point ({tok})"
        else:
            s += f"({tok})"
        first = False
        prev = tok
    return s


# --------------------------------------------------------------------------- #
# The parser
# --------------------------------------------------------------------------- #


class CorpusParser:
    """Parse one language of the consolidated AI Act (+ recitals from the OJ text)."""

    def __init__(self, lang: str) -> None:
        if lang not in ("en", "it"):
            raise ValueError(f"unsupported language: {lang}")
        self.lang = lang
        self.state: Amend | None = None
        self.nodes: list[Node] = []
        self.by_id: dict[str, Node] = {}
        self.warnings: list[str] = []
        self._order = 0

    # -- amendment markers ------------------------------------------------- #
    def _modref(self, p: etree._Element) -> Del | None:
        """Update ``self.state`` from a ``p.modref`` element; return a Del event if deleted."""
        a = next(p.iter("{*}a"), None)
        txt = _WS_RE.sub(" ", "".join(p.itertext())).strip()
        title = (a.get("title") or "") if a is not None else ""
        m = re.search(r"(?:▼|►)\s*([MBC]\d*)", txt)
        marker = m.group(1) if m else "B"
        if marker.startswith("B") or not title or ":" not in title:
            self.state = None
            return None
        by, kind = [x.strip() for x in title.split(":", 1)]
        kind = kind.lower()
        if kind not in ("replaced", "inserted", "deleted"):
            self.warnings.append(f"unknown amendment kind {title!r}")
            kind = "replaced"
        self.state = Amend(marker, kind, by)
        if kind == "deleted":
            ev = Del(self.state)
            self.state = None
            return ev
        return None

    # -- eager scanning ------------------------------------------------------ #
    def scan(self, el: etree._Element, strip_label: str | None = None) -> list[Any]:
        """Scan the children of ``el`` in document order into events."""
        events: list[Any] = []
        buf: list[str] = [el.text or ""] if _ln(el) else []

        def flush() -> None:
            s = _norm("".join(buf))
            buf.clear()
            if s:
                events.append(Text(s))

        for ch in el:
            tag = _ln(ch)
            c = _cls(ch)
            if not tag:  # comment / PI
                buf.append(ch.tail or "")
                continue
            if tag in _INLINE_TAGS and "no-parag" not in c:
                buf.append(_raw_text(ch, with_tail=False))
                buf.append(ch.tail or "")
                continue
            if "no-parag" in c:
                buf.append(ch.tail or "")
                continue
            flush()
            self._block(ch, tag, c, events)
            buf.append(ch.tail or "")
        flush()
        if strip_label:
            for i, ev in enumerate(events):
                if isinstance(ev, Text):
                    s = ev.s
                    if s.startswith(strip_label):
                        s = s[len(strip_label) :].lstrip()
                    ev.s = s
                    if not s:
                        del events[i]
                    break
        return events

    def _block(self, ch: etree._Element, tag: str, c: str, events: list[Any]) -> None:
        if tag == "p":
            if "modref" in c:
                d = self._modref(ch)
                if d:
                    events.append(d)
            elif c.startswith("title-gr-seq-level"):
                lvl = int(c.rsplit("-", 1)[1])
                s = text_of(ch)
                if s:
                    events.append(Head(lvl, s))
            elif c.startswith(("title-annex", "title-article", "title-division", "footnote")):
                pass
            else:
                s = text_of(ch)
                if s:
                    events.append(Text(s))
        elif tag == "div":
            if "eli-title" in c:
                return
            if "grid-container" in c:
                events.append(self._grid_item(ch))
            elif "norm" in c and any("no-parag" in _cls(x) for x in ch if _ln(x) == "span"):
                span = next(x for x in ch if _ln(x) == "span" and "no-parag" in _cls(x))
                raw = _norm("".join(span.itertext()))
                tok = token_of(raw)
                if tok and re.fullmatch(r"\d+[a-z]?|[a-z]{1,3}|\d+(\.\d+)+", tok) and not raw.lstrip().startswith(("‘", "“", "«")):
                    events.append(Item(raw, tok, "parag", self.state, self.scan(ch)))
                else:
                    sub = self.scan(ch)
                    if sub and isinstance(sub[0], Text):
                        sub[0].s = f"{raw} {sub[0].s}".strip()
                    else:
                        sub.insert(0, Text(raw))
                    events.extend(sub)
            elif "centered" in c:
                for t in ch.iter("{*}table"):
                    s = _table_text(t)
                    if s:
                        events.append(Text(s))
            elif not c:
                full = text_of(ch)
                m = _LABEL_RE.match(full + " ")
                if m and _ln(ch) == "div":
                    raw = m.group(1)
                    tok = token_of(raw)
                    if tok:
                        events.append(Item(raw, tok, "plain", self.state, self.scan(ch, strip_label=raw)))
                        return
                events.extend(self.scan(ch))
            else:
                events.extend(self.scan(ch))
        elif tag == "table":
            s = _table_text(ch)
            if s:
                events.append(Text(s))

    def _grid_item(self, ch: etree._Element) -> Item:
        col1 = next((x for x in ch if "grid-list-column-1" in _cls(x)), None)
        col2 = next((x for x in ch if "grid-list-column-2" in _cls(x)), None)
        raw = text_of(col1) if col1 is not None else ""
        state = self.state
        events = self.scan(col2) if col2 is not None else []
        return Item(raw, token_of(raw), "grid", state, events)

    # -- node creation -------------------------------------------------------- #
    def _new(
        self,
        id_: str,
        type_: str,
        segs: list[tuple[str, str]],
        parent: Node | None,
        amend: Amend | None,
        *,
        src: str = "",
        plain: bool = False,
        text: str = "",
        ctx: dict[str, Any] | None = None,
    ) -> Node:
        if id_ in self.by_id:
            self.warnings.append(f"duplicate id {id_}")
            n = 2
            while f"{id_}~{n}" in self.by_id:
                n += 1
            id_ = f"{id_}~{n}"
        self._order += 1
        node = Node(id_, type_, segs, parent, amend, src=src, plain=plain, order=self._order)
        if text:
            node.text_parts.append(text)
        node.ctx = dict(ctx) if ctx else (dict(parent.ctx) if parent else {})
        if parent:
            parent.children.append(node)
        self.nodes.append(node)
        self.by_id[id_] = node
        return node

    # -- container filling ---------------------------------------------------- #
    def fill(self, root: Node, events: list[Any]) -> None:
        """Turn events into child nodes of ``root`` (recursively)."""
        is_top = root.type in ("article", "annex")
        is_annex = root.type == "annex"
        stack: list[Node] = [root]
        last_num: dict[str, int] = {}
        last_item: Node | None = None
        pending_del: Amend | None = None
        awaiting_title: Node | None = None
        synth: dict[str, int] = {}

        def scope() -> Node:
            return stack[-1]

        def cont_par() -> Node | None:
            """Numbered paragraph that unnumbered article-level content continues."""
            sc = scope()
            if sc.type == "article" and last_item is not None and last_item.src == "parag":
                return last_item
            return None

        def add_text(s: str) -> None:
            sc = scope()
            cp = cont_par()
            if cp is not None:
                (cp.tail_parts if cp.children else cp.text_parts).append(s)
            elif last_item is not None and last_item.parent is sc:
                if last_item.type == "paragraph" or last_item.plain:
                    last_item.tail_parts.append(s)
                else:
                    sc.tail_parts.append(s)
            elif sc.children:
                sc.tail_parts.append(s)
            elif sc.type in ("article", "annex"):
                sc.body_parts.append(s)
            else:
                sc.text_parts.append(s)

        def child_kind(parent: Node, item_src: str, tok: str) -> tuple[str, str, str]:
            """Return (node type, seg kind, relative id token)."""
            if parent.segs[0][0] == "art":
                if parent.type == "article" and item_src == "parag":
                    return "paragraph", "par", tok
                return "point", "pt", tok
            ptok = parent.segs[-1][1] if len(parent.segs) > 1 else None
            rel = tok
            if ptok and tok.startswith(ptok + "."):
                rel = tok[len(ptok) + 1 :]
            return "annex_point", "apt", rel

        def make_item(parent: Node, tok: str, src: str, amend: Amend | None, plain: bool) -> Node:
            ntype, skind, rel = child_kind(parent, src, tok)
            full_tok = tok
            if rel in parent.seen:  # list restarts: a further sub-paragraph of the same node
                parent.group += 1
                parent.seen = set()
            parent.seen.add(rel)
            if parent.group > 1:
                rel = f"{rel}-{parent.group}"
            node = self._new(
                f"{parent.id}.{rel}", ntype, parent.segs + [(skind, full_tok)], parent, amend,
                src=src, plain=plain,
            )
            return node

        def flush_del(upto: int | None = None) -> None:
            nonlocal pending_del
            if pending_del is None:
                return
            sc = scope()
            start = last_num.get(sc.id, 0) + 1
            nums = range(start, upto) if upto is not None and upto > start else [start]
            for n in nums:
                make_item(sc, str(n), "parag" if sc.type == "article" else "plain", pending_del, False)
                last_num[sc.id] = n
            pending_del = None

        for ev in events:
            if isinstance(ev, Text):
                add_text(ev.s)
            elif isinstance(ev, Del):
                flush_del()
                pending_del = ev.amend
            elif isinstance(ev, Head):
                flush_del()
                last_item = None
                s = ev.s
                msec = re.match(r"^(?:Section|Sezione)\s+([A-Za-z0-9]+)\s*(?:[.:\-–—]\s*)?(.*)$", s)
                mnum = re.match(r"^(\d+)\.\s*(.*)$", s)
                mlet = re.match(r"^([a-z])[.)]\s*(.*)$", s)
                if msec and ev.level == 1:
                    del stack[1:]
                    tok = msec.group(1).lower()
                    node = self._new(
                        f"{root.id}.{msec.group(1).upper() if len(tok) == 1 and tok.isalpha() else tok}",
                        "annex_point", root.segs + [("sec", msec.group(1).upper() if tok.isalpha() else tok)],
                        root, self.state, text=msec.group(2).strip(),
                    )
                    node.heading_level = 1
                    stack.append(node)
                    awaiting_title = node if not msec.group(2).strip() else None
                elif awaiting_title is not None and not mnum:
                    awaiting_title.text_parts.append(s.rstrip("."))
                    awaiting_title = None
                elif mnum and ev.level == 1:
                    while len(stack) > 1 and stack[-1].segs[-1][0] != "sec":
                        stack.pop()
                    parent = scope()
                    node = make_item(parent, mnum.group(1), "plain", self.state, False)
                    node.text_parts.append(mnum.group(2).rstrip("."))
                    node.heading_level = 1
                    stack.append(node)
                elif mlet and ev.level == 2:
                    while len(stack) > 1 and stack[-1].heading_level != 1:
                        stack.pop()
                    parent = scope()
                    node = make_item(parent, mlet.group(1), "plain", self.state, False)
                    node.text_parts.append(mlet.group(2).rstrip("."))
                    node.heading_level = 2
                    stack.append(node)
                else:
                    add_text(s)
            elif isinstance(ev, Item):
                sc = scope()
                tok = ev.token
                if tok is None:  # bullets / dashes: synthetic running number
                    synth[sc.id] = synth.get(sc.id, 0) + 1
                    tok = str(synth[sc.id])
                container = sc
                cp = cont_par()
                if cp is not None and ev.src != "parag":
                    container = cp
                elif (
                    ev.src == "grid"
                    and _is_alpha(tok)
                    and last_item is not None
                    and last_item.plain
                    and last_item.parent is sc
                ):
                    container = last_item
                if container is sc and tok.isdigit():
                    flush_del(int(tok))
                    last_num[sc.id] = int(tok)
                node = make_item(container, tok, ev.src, ev.amend, ev.src == "plain")
                self.fill(node, ev.events)
                if container is sc:
                    last_item = node
        flush_del()
        _ = is_top

    @staticmethod
    def _descendants(n: Node) -> list[Node]:
        out: list[Node] = []
        for c in n.children:
            out.append(c)
            out.extend(CorpusParser._descendants(c))
        return out

    # -- document-level walkers ----------------------------------------------- #
    def _article(self, el: etree._Element, ctx: dict[str, Any]) -> None:
        num = (el.get("id") or "")[len("art_") :]
        title_el = next(el.iter("{*}p"), None)
        tit = ""
        for p in el.iter("{*}p"):
            if "stitle-article" in _cls(p):
                tit = text_of(p)
                break
        _ = title_el
        c = dict(ctx)
        c["title"] = tit
        node = self._new(f"art:{num}", "article", [("art", num)], None, self.state, text=tit, ctx=c)
        self.fill(node, self.scan(el))

    def _annex(self, el: etree._Element) -> None:
        num = (el.get("id") or "")[len("anx_") :]
        heads = [text_of(p) for p in el.iter("{*}p") if _cls(p).startswith("title-annex")]
        title = " ".join(heads[1:]).strip()
        node = self._new(f"annex:{num}", "annex", [("annex", num)], None, self.state, text=title, ctx={"title": title})
        self.fill(node, self.scan(el))
        if not title and node.body_parts:  # e.g. Annex XIV has no separate title
            title = node.body_parts[0]
            node.text_parts[:] = [title]
            node.ctx["title"] = title
            for ch in self._descendants(node):
                ch.ctx["title"] = title

    def _walk(self, el: etree._Element, ctx: dict[str, Any]) -> None:
        for ch in el:
            tag = _ln(ch)
            if not tag:
                continue
            c = _cls(ch)
            cid = ch.get("id") or ""
            if tag == "p" and "modref" in c:
                self._modref(ch)
            elif tag == "div" and cid.startswith("cpt_"):
                ids = cid[len("cpt_") :]
                nctx = dict(ctx)
                t1 = next((x for x in ch if _cls(x) == "title-division-1"), None)
                t2 = next((x for x in ch if _cls(x) == "title-division-2"), None)
                title = sentence_case(text_of(t2)) if t2 is not None else None
                if ".sct_" in ids:
                    nctx["section"] = ids.split(".sct_")[1]
                    nctx["section_title"] = title
                else:
                    nctx.update(chapter=ids, chapter_title=title, section=None, section_title=None)
                _ = t1
                self._walk(ch, nctx)
            elif tag == "div" and cid.startswith("art_") and "eli-subdivision" in c:
                self._article(ch, ctx)
            elif tag == "div" and cid.startswith("anx_"):
                self._annex(ch)
            elif tag == "div" and cid.startswith("enc_"):
                self._walk(ch, {})
            elif tag == "div" and (cid.startswith("fnp_") or "eli-main-title" in c):
                continue
            elif tag == "div":
                self._walk(ch, ctx)

    def parse_consolidated(self, path: Path) -> None:
        """Parse articles and annexes from the consolidated XHTML."""
        root = etree.parse(str(path), etree.XMLParser(recover=True, huge_tree=True)).getroot()
        container = next((e for e in root.iter("{*}div") if "eli-container" in _cls(e)), None)
        if container is None:
            raise ValueError(f"{path}: eli-container not found")
        self.state = None
        self._walk(container, {})

    def parse_recitals(self, path: Path) -> None:
        """Parse recitals ``(1)``-``(180)`` from the original OJ XHTML."""
        root = etree.parse(str(path), etree.XMLParser(recover=True, huge_tree=True)).getroot()
        recs: list[tuple[int, str]] = []
        for div in root.iter("{*}div"):
            cid = div.get("id") or ""
            if not re.fullmatch(r"rct_\d+", cid) or "eli-subdivision" not in _cls(div):
                continue
            num = int(cid[4:])
            tds = list(div.iter("{*}td"))
            if len(tds) < 2:
                self.warnings.append(f"recital {num}: unexpected structure")
                continue
            content = tds[1]
            parts: list[str] = []

            def blocks(n: etree._Element) -> None:
                for ch in n:
                    t = _ln(ch)
                    if t == "p":
                        s = text_of(ch)
                        if s:
                            parts.append(s)
                    elif t == "table":
                        for tr in ch.iter("{*}tr"):
                            cells = [text_of(td) for td in tr if _ln(td) in ("td", "th")]
                            line = " ".join(x for x in cells if x)
                            if line:
                                parts.append(line)
                    elif t in ("div", "td", "tbody", "tr"):
                        blocks(ch)

            blocks(content)
            if not parts:
                parts.append(text_of(content))
            recs.append((num, "\n".join(parts)))
        recs.sort()
        for num, text in recs:
            node = self._new(f"rec:{num}", "recital", [("rec", str(num))], None, None, text=text, ctx={})
            _ = node

    # -- output ------------------------------------------------------------------ #
    def provisions(self) -> list[dict[str, Any]]:
        """Serialise nodes (in document order) into contract-shaped dicts."""
        out: list[dict[str, Any]] = []
        for n in sorted(self.nodes, key=lambda x: x.order):
            segs = n.segs
            kind0 = segs[0][0]
            ctx = n.ctx
            art = par = pt = ann = rec = None
            if kind0 == "art":
                a = segs[0][1]
                art = int(a) if a.isdigit() else a
                par = next((t for k, t in segs if k == "par"), None)
                ps = [t for k, t in segs if k == "pt"]
                pt = ".".join(ps) if ps else None
            elif kind0 == "annex":
                ann = segs[0][1]
                rest = [t for k, t in segs[1:]]
                pt = ".".join(rest) if rest else None
            else:
                rec = int(segs[0][1])
            text = "\n".join(n.text_parts)
            body = "\n".join(n.body_parts) or None
            tail = "\n".join(n.tail_parts) or None
            if n.type in ("article", "annex"):
                text = n.text_parts[0] if n.text_parts else ""
            if n.amend and n.amend.kind == "deleted":
                text, body, tail = "", None, None
            out.append(
                {
                    "id": n.id,
                    "type": n.type,
                    "label": make_label(segs, self.lang),
                    "parent_id": n.parent.id if n.parent else None,
                    "children": [c.id for c in n.children],
                    "article": art,
                    "paragraph": par,
                    "point": pt,
                    "annex": ann,
                    "recital": rec,
                    "chapter": ctx.get("chapter") if kind0 == "art" else None,
                    "chapter_title": ctx.get("chapter_title") if kind0 == "art" else None,
                    "section": ctx.get("section") if kind0 == "art" else None,
                    "section_title": ctx.get("section_title") if kind0 == "art" else None,
                    "title": ctx.get("title") if kind0 != "rec" else None,
                    "text": text,
                    "body": body,
                    "text_after": tail,
                    "original_text": None,
                    "amendment": n.amend.as_dict() if n.amend else None,
                    "order": n.order,
                }
            )
        return out


def parse_corpus(
    consolidated: Path,
    original: Path,
    lang: str,
    retrieved_at: str,
) -> tuple[dict[str, Any], list[str]]:
    """Parse one language and return ``(corpus_dict, warnings)``."""
    p = CorpusParser(lang)
    p.parse_recitals(original)
    p.parse_consolidated(consolidated)
    provs = p.provisions()
    # Recitals come first in document order (preamble), then articles, then annexes.
    counts = {
        "articles": sum(1 for x in provs if x["type"] == "article"),
        "annexes": sum(1 for x in provs if x["type"] == "annex"),
        "recitals": sum(1 for x in provs if x["type"] == "recital"),
        "provisions": len(provs),
    }
    meta = {
        "celex": CELEX,
        "language": lang,
        "consolidated_as_of": "2026-07-27",
        "retrieved_at": retrieved_at,
        "source_url": SOURCE_URL,
        "eurlex_url": ELI_URL,
        "amending_acts": AMENDING_ACTS,
        "counts": counts,
        "notes": {
            "recitals_source": "Official Journal text of Regulation (EU) 2024/1689 (CELEX 32024R1689); "
            "EUR-Lex consolidations omit the preamble.",
        },
    }
    return {"meta": meta, "provisions": provs}, p.warnings
