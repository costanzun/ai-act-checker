#!/usr/bin/env python3
"""Build data/guidance/<slug>.json from the PDFs/HTML in data/raw/guidance/.

No network access: downloads are done separately (see docs/guidance-sources.md).
Run with:  backend/.venv/bin/python -I scripts/build_guidance.py [slug ...]

Strategy (PDF guidelines): extract text per page with pypdf, drop table-of-contents
pages (and use their numbers to validate body headings), drop footnote blocks at
the bottom of each page, detect numbered headings (1., 2.1., 3.2.1.; Roman
numerals for the high-risk draft), then split each section on the Commission's
numbered paragraphs "(N)" into chunks of roughly <= 300 words.
"""
from __future__ import annotations

import json
import re
import sys
from collections import Counter
from pathlib import Path

from pypdf import PdfReader
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw" / "guidance"
OUT = ROOT / "data" / "guidance"
RETRIEVED = "2026-11-03"
CHUNK_WORDS = 300
MAX_PARA_WORDS = 450

DOCS = {
    "ai-system-definition-2025": dict(
        title="Commission Guidelines on the definition of an AI system (2025)",
        short="Commission Guidelines on the AI system definition (2025)",
        status="final", date="2025-02-06", ref="C(2025) 924 (formally adopted as C(2025) 5053, 29.7.2025)",
        source_url="https://digital-strategy.ec.europa.eu/en/library/commission-publishes-guidelines-ai-system-definition-facilitate-first-ai-acts-rules-application",
        files=[("ai-system-definition-2025.en.pdf", "", "https://ec.europa.eu/newsroom/dae/redirection/document/112455")],
        mode="pdf"),
    "prohibited-practices-2025": dict(
        title="Commission Guidelines on prohibited artificial intelligence practices (2025)",
        short="Commission Guidelines on prohibited practices (2025)",
        status="final", date="2025-02-04", ref="C(2025) 884 (approved C(2025) 5052, 29.7.2025)",
        source_url="https://digital-strategy.ec.europa.eu/en/library/commission-publishes-guidelines-prohibited-artificial-intelligence-ai-practices-defined-ai-act",
        files=[("prohibited-practices-2025.en.pdf", "", "https://ec.europa.eu/newsroom/dae/redirection/document/112367")],
        mode="pdf"),
    "gpai-obligations-2025": dict(
        title="Commission Guidelines on the scope of the obligations for providers of general-purpose AI models (2025)",
        short="Commission Guidelines on GPAI model obligations (2025)",
        status="final", date="2025-07-18", ref="C(2025) 5045",
        source_url="https://digital-strategy.ec.europa.eu/en/library/guidelines-scope-obligations-providers-general-purpose-ai-models-under-ai-act",
        files=[("gpai-obligations-2025.en.pdf", "", "https://ec.europa.eu/newsroom/dae/redirection/document/118340")],
        mode="pdf"),
    "high-risk-classification-2026-draft": dict(
        title="Draft Commission Guidelines on the classification of high-risk AI systems (Article 6)",
        short="Draft Commission Guidelines on high-risk classification (2026)",
        status="draft", date="2026-05-19", ref="draft for stakeholder consultation",
        source_url="https://digital-strategy.ec.europa.eu/en/library/draft-commission-guidelines-classification-high-risk-ai-systems",
        files=[
            ("high-risk-classification-2026-draft.general.pdf", "general", "https://ec.europa.eu/newsroom/dae/redirection/document/128559"),
            ("high-risk-classification-2026-draft.annex1.pdf", "annex1", "https://ec.europa.eu/newsroom/dae/redirection/document/128560"),
            ("high-risk-classification-2026-draft.annex3.pdf", "annex3", "https://ec.europa.eu/newsroom/dae/redirection/document/128561"),
        ],
        mode="pdf", roman=True),
    "transparency-art50-2026": dict(
        title="Commission Guidelines on the transparency obligations for certain AI systems under Article 50 (2026)",
        short="Commission Guidelines on Art. 50 transparency (2026)",
        status="final", date="2026-07-20", ref="C(2026) 5054",
        source_url="https://digital-strategy.ec.europa.eu/en/library/guidelines-transparency-obligations-providers-and-deployers-ai-systems",
        files=[("transparency-art50-2026.en.pdf", "", "https://ec.europa.eu/newsroom/dae/redirection/document/131215")],
        mode="pdf"),
    "code-of-practice-ai-content-2026": dict(
        title="Code of Practice on marking and labelling of AI-generated content (transparency of AI-generated content)",
        short="Code of Practice on AI-generated content (2026)",
        status="final", date="2026-06-10", ref="voluntary code; Commission opinion of 9.7.2026",
        source_url="https://digital-strategy.ec.europa.eu/en/policies/code-practice-ai-generated-content",
        files=[("code-of-practice-ai-generated-content-2026.pdf", "", "https://ec.europa.eu/newsroom/dae/redirection/document/129555")],
        mode="code"),
    "ai-omnibus-2026": dict(
        title="Commission web pages on the Digital Omnibus on AI (Regulation (EU) 2026/1744)",
        short="Commission AI Omnibus news item (2026)",
        status="final", date="2026-07-27", ref="Regulation (EU) 2026/1744",
        source_url="https://digital-strategy.ec.europa.eu/en/news/ai-omnibus-enters-force",
        files=[("omnibus-ai-enters-force.html", "news", "https://digital-strategy.ec.europa.eu/en/news/ai-omnibus-enters-force")],
        mode="html"),
    "ai-omnibus-faq-2026": dict(
        title="AI Act Service Desk FAQ - Digital Omnibus category (describes the November 2025 proposal)",
        short="AI Act Service Desk FAQ on the Digital Omnibus",
        status="final", date="2025-11-19", ref="Service Desk FAQ (proposal stage; undated page)",
        source_url="https://ai-act-service-desk.ec.europa.eu/en/faq?combine=&faq_category_id=99",
        files=[("omnibus-faq.html", "faq", "https://ai-act-service-desk.ec.europa.eu/en/faq?combine=&faq_category_id=99")],
        mode="faq"),
}

ROMAN = ["I", "II", "III", "IV", "V", "VI", "VII", "VIII"]
FOOT_START = re.compile(r"^(\d{1,3})\s+[A-Z‘“(]")
HEAD_RE = re.compile(r"^(\d+(?:\.\d+)*)\.?\s+(\S.*)$")
ROMAN_RE = re.compile(r"^(I|II|III|IV|V|VI|VII|VIII)\.\s+(\S.*)$")
PARA_RE = re.compile(r"^\((\d{1,3})\)\s")


# ---------------------------------------------------------------- text helpers
def words(s: str) -> int:
    return len(s.split())


def clean(text: str) -> str:
    text = text.replace("­", "").replace("\xa0", " ")
    text = re.sub(r"(?<=[A-Za-z]) -(?=[a-z])", "-", text)       # "high -risk" -> "high-risk"
    text = re.sub(r"(?<=[a-z])- (?=[a-z])", "-", text)           # "general- purpose"
    text = re.sub(r"\b10 ?\^?(2[2-7])(?=\s*(?:FLOP|floating))", r"10^\1", text)  # superscript lost in extraction
    text = re.sub(r"\s+", " ", text).strip()
    return text


VALID_SHORT = set("a i an as at be by do go if in is it me my no of on or so to up us we am he".split())


def fix_spaces(txt: str, vocab: Counter) -> str:
    """Repair justified-text artefacts ('s ystemic', 'ca n', 'wi ll') using the
    document's own vocabulary: join a short non-word fragment to the next token
    when the joined form is a word seen at least twice in the document."""
    def repl(m):
        x, y = m.group(1), m.group(2)
        j = (x + y).lower()
        if vocab[j] < 2:
            return m.group(0)
        xl, yl = x.lower(), y.lower()
        if xl in VALID_SHORT:
            ok = vocab[j] >= 20 and ((len(y) == 1 and yl not in "ai") or (len(y) == 2 and yl not in VALID_SHORT))
            return x + y if ok else m.group(0)
        if xl == "o" and len(y) > 2:       # bullet marker
            return m.group(0)
        return x + y
    return re.sub(r"\b([A-Za-z]{1,3}) ([a-z]{1,10})\b", repl, txt)


FOOT_PAREN = re.compile(r"^\((\d{1,3})\)\s+(See|Article|Articles|Commission|Regulation|Recital|Judgment|Case|Directive|Communication|Ibid|Idem|Council|European|Proposal|Rules|Decision|Opinion|Guidelines|OECD|ISO|For|Cf)\b")


class FootState:
    """Tracks the last numbered body paragraph '(N)' so that footnotes written
    as '(N) See ...' can be told apart from body paragraphs."""
    last_para = 0


def strip_footnotes(page_lines: list[str], st: FootState | None = None) -> list[str]:
    """Drop the footnote block at the bottom of the page (starts at the first
    'N Capitalised...' / '(N) See ...' line in the lower half; page numbers are on top)."""
    n = len(page_lines)
    st = st or FootState()
    for i, l in enumerate(page_lines):
        m = PARA_RE.match(l.strip())
        if i < n // 2 and m:
            st.last_para = int(m.group(1))
    for i in range(n // 2, n):
        line = page_lines[i].strip()
        m = FOOT_START.match(line)
        if m and int(m.group(1)) <= 250:
            return page_lines[:i]
        m = FOOT_PAREN.match(line)
        if m and int(m.group(1)) != st.last_para + 1:
            return page_lines[:i]
        pm = PARA_RE.match(line)
        if pm:
            st.last_para = int(pm.group(1))
    return page_lines


def read_pages(path: Path) -> list[list[str]]:
    pages = []
    for p in PdfReader(str(path)).pages:
        lines = [l.rstrip() for l in (p.extract_text() or "").splitlines()]
        pages.append(lines)
    return pages


def split_toc(pages: list[list[str]]):
    """Return (toc_numbers or None, body_pages). A TOC page has >=3 dot-leader
    lines; everything up to its last leader line is dropped (text after it, e.g.
    the start of the introduction, is kept)."""
    toc_numbers: set[str] = set()
    body = []
    for p in pages:
        leaders = [i for i, l in enumerate(p) if re.search(r"\.{5,}", l)]
        if len(leaders) >= 3:
            for l in p[: leaders[-1] + 1]:
                m = HEAD_RE.match(l.strip())
                if m:
                    toc_numbers.add(m.group(1))
            body.append(p[leaders[-1] + 1:])
        else:
            body.append(p)
    return (toc_numbers or None), body


# ------------------------------------------------------------ section building
def valid_next(stack: list[int], nums: list[int]) -> bool:
    if not stack:
        return nums == [1]
    if len(nums) == len(stack) + 1:
        return nums[:-1] == stack and nums[-1] == 1
    if len(nums) <= len(stack):
        k = len(nums)
        return nums[:-1] == stack[: k - 1] and nums[-1] == stack[k - 1] + 1
    return False


def parse_pdf_sections(path: Path, roman: bool):
    """Yield dicts: num (str), title, lines (list[str])."""
    pages = read_pages(path)
    toc_numbers, body = split_toc(pages)
    lines: list[str] = []
    st = FootState()
    for p in body:
        p = [l for l in p if l.strip()]
        if p and re.fullmatch(r"\d{1,3}", p[0].strip()):   # running page number
            p = p[1:]
        p = [l for l in p if l.strip() not in ("EN EN", "EN", "ANNEX")]
        lines.extend(strip_footnotes(p, st))

    sections = []
    cur = None
    stack: list[int] = []
    rom = -1
    i = 0
    while i < len(lines):
        raw = lines[i].strip()
        head = None
        if roman:
            m = ROMAN_RE.match(raw)
            if m and ROMAN.index(m.group(1)) == rom + 1 and len(raw) < 140:
                head = (m.group(1), m.group(2), "roman")
        if head is None:
            m = HEAD_RE.match(raw)
            if m and not re.search(r"\.{4,}", raw) and len(raw) < 200:
                num = m.group(1)
                nums = [int(x) for x in num.split(".")]
                title = m.group(2)
                if (valid_next(stack, nums) and not title.rstrip().endswith(";")
                        and title[0] in "ABCDEFGHIJKLMNOPQRSTUVWXYZ‘'“("
                        and (toc_numbers is None or num in toc_numbers)):
                    head = (num, title, "arabic")
        if head:
            num, title, kind = head
            # wrapped heading continuation: following lines starting lowercase
            j = i + 1
            while j < len(lines) and j < i + 3 and re.match(r"^[a-z]", lines[j].strip()) \
                    and not title.rstrip().endswith((".", ":", ";")):
                title += " " + lines[j].strip()
                j += 1
            i = j - 1
            if kind == "roman":
                rom += 1
                stack = []
                cur = dict(num=head[0], title=clean(title), lines=[])
            else:
                stack = [int(x) for x in num.split(".")]
                cur = dict(num=(ROMAN[rom] + "." if rom >= 0 and roman else "") + num,
                           title=clean(title), lines=[])
            sections.append(cur)
        elif cur is not None:
            cur["lines"].append(raw)
        i += 1
    return sections


def parse_code_sections(path: Path):
    _, pages = split_toc(read_pages(path))
    lines = []
    for p in pages:
        p = [l for l in p if l.strip() and not re.search(r"\.{5,}", l)]
        if p and re.fullmatch(r"\d{1,3}", p[0].strip()):
            p = p[1:]
        lines.extend(strip_footnotes(p))
    sections, cur, sec = [], None, 1
    started = False
    for raw in (l.strip() for l in lines):
        ms = re.match(r"^Section (\d): [A-Z]", raw)
        if ms:
            if int(ms.group(1)) != sec:
                cur = None            # section cover / preamble text is not part of a measure
            sec = int(ms.group(1))
        if raw == "Annex":
            cur = None
        if raw == "Glossary" and started:
            cur = dict(num="glossary", title="Glossary", lines=[])
            sections.append(cur)
            continue
        mc = re.match(r"^Commitment (\d+): (.+)$", raw)
        mm = re.match(r"^Measure (\d+\.\d+): (.+)$", raw)
        if mc or mm:
            started = True
            if mc:
                cur = dict(num=f"sec{sec}.commitment-{mc.group(1)}", title=f"Section {sec}, Commitment {mc.group(1)}: {clean(mc.group(2))}", lines=[])
            else:
                cur = dict(num=f"sec{sec}.measure-{mm.group(1)}", title=f"Section {sec}, Measure {mm.group(1)}: {clean(mm.group(2))}", lines=[])
            sections.append(cur)
        elif cur is not None and started:
            cur["lines"].append(raw)
    return sections


def parse_html_sections(path: Path):
    soup = BeautifulSoup(path.read_text(encoding="utf-8"), "lxml")
    main = soup.find("main") or soup
    sections, cur = [], None
    for el in main.find_all(["h1", "h2", "h3", "p", "li"]):
        t = clean(el.get_text(" "))
        if not t:
            continue
        if el.name in ("h1", "h2", "h3"):
            cur = dict(num=str(len(sections) + 1), title=t, lines=[])
            sections.append(cur)
        elif cur is not None:
            cur["lines"].append(t)
    return sections


def parse_faq_sections(path: Path):
    soup = BeautifulSoup(path.read_text(encoding="utf-8"), "lxml")
    sections = []
    for d in soup.find_all("details"):
        q = d.find("summary")
        if not q:
            continue
        qt = clean(q.get_text(" "))
        qt = re.sub(r"^Digital Omnibus\s+", "", qt)
        body = [clean(e.get_text(" ")) for e in d.find_all(["p", "li"])]
        sections.append(dict(num=str(len(sections) + 1), title=qt, lines=[b for b in body if b]))
    return sections


def paragraphs(lines: list[str]) -> list[tuple[str | None, str]]:
    """Group lines into Commission-numbered paragraphs '(N)'; else one block."""
    paras: list[tuple[str | None, list[str]]] = []
    for l in lines:
        m = PARA_RE.match(l)
        if m or not paras:
            paras.append((m.group(1) if m else None, [l]))
        else:
            paras[-1][1].append(l)
    out = []
    for n, ls in paras:
        txt = clean(" ".join(ls))
        txt = re.sub(r"(?<=\w)- (?=[a-z])", "-", txt)
        out.append((n, txt))
    return out


def sentences(txt: str) -> list[str]:
    return re.split(r"(?<=[.;:?!])\s+(?=[A-Z‘“(])", txt)


def chunk_section(lines: list[str]) -> list[tuple[str, list[str]]]:
    """Return list of (text, [para numbers])."""
    units: list[tuple[str | None, str]] = []
    for n, txt in paragraphs(lines):
        if words(txt) > MAX_PARA_WORDS:
            buf, cnt = [], 0
            for s in sentences(txt):
                buf.append(s)
                cnt += words(s)
                if cnt >= CHUNK_WORDS:
                    units.append((n, " ".join(buf)))
                    buf, cnt = [], 0
            if buf:
                units.append((n, " ".join(buf)))
        else:
            units.append((n, txt))
    chunks, cur, cnt, nums = [], [], 0, []
    for n, t in units:
        w = words(t)
        if cur and cnt + w > CHUNK_WORDS * 1.25:
            chunks.append((" ".join(cur), nums))
            cur, cnt, nums = [], 0, []
        cur.append(t)
        cnt += w
        if n and n not in nums:
            nums.append(n)
    if cur:
        chunks.append((" ".join(cur), nums))
    return chunks


def build(slug: str) -> dict:
    cfg = DOCS[slug]
    provisions = []
    order = 0
    for fname, prefix, url in cfg["files"]:
        path = RAW / fname
        if not path.exists():
            raise SystemExit(f"missing {path}")
        if cfg["mode"] == "pdf":
            secs = parse_pdf_sections(path, cfg.get("roman", False))
        elif cfg["mode"] == "code":
            secs = parse_code_sections(path)
        elif cfg["mode"] == "faq":
            secs = parse_faq_sections(path)
        else:
            secs = parse_html_sections(path)
        vocab = Counter(w.lower() for s in secs for l in s["lines"] for w in re.findall(r"[A-Za-z]+", l))
        for s in secs:
            chunks = chunk_section(s["lines"]) if s["lines"] else []
            chunks = [(fix_spaces(t, vocab), n) for t, n in chunks]
            chunks = [c for c in chunks if words(c[0]) >= 12]
            if cfg["mode"] in ("html", "faq"):
                chunks = [(" ".join(c[0] for c in chunks), [])] if chunks else []
            base = f"{prefix}.{s['num']}" if prefix and cfg["mode"] not in ("html", "faq") else s["num"]
            for k, (txt, nums) in enumerate(chunks, 1):
                pid = f"guid:{slug}.{base}" + (f".p{k}" if len(chunks) > 1 else "")
                if cfg["mode"] == "code":
                    sec_lbl = s["title"].split(":")[0]
                else:
                    sec_lbl = "§" + s["num"]
                part = f" (part {k}/{len(chunks)})" if len(chunks) > 1 else ""
                part_name = {"general": "general principles", "annex1": "Annex I part", "annex3": "Annex III part"}.get(prefix, "")
                label = f"{cfg['short']}{', ' + part_name if part_name else ''}, {sec_lbl}{part}"
                order += 1
                provisions.append({
                    "id": pid, "type": "guidance", "label": label,
                    "parent_id": None, "children": [],
                    "title": s["title"], "text": txt, "order": order,
                    "meta": {
                        "binding": False, "status": cfg["status"],
                        "source_url": cfg["source_url"], "file_url": url,
                        "date": cfg["date"], "retrieved_at": RETRIEVED,
                        "document": cfg["title"], "reference": cfg["ref"],
                        "language": "en", "section": s["num"],
                        "paragraphs": (f"({nums[0]})-({nums[-1]})" if len(nums) > 1 else (f"({nums[0]})" if nums else None)),
                    },
                })
    return {
        "meta": {
            "slug": slug, "type": "guidance", "title": cfg["title"], "binding": False,
            "status": cfg["status"], "date": cfg["date"], "reference": cfg["ref"],
            "source_url": cfg["source_url"], "retrieved_at": RETRIEVED, "language": "en",
            "counts": {"provisions": len(provisions)},
        },
        "provisions": provisions,
    }


def main(argv: list[str]) -> None:
    slugs = argv or list(DOCS)
    OUT.mkdir(parents=True, exist_ok=True)
    for slug in slugs:
        data = build(slug)
        (OUT / f"{slug}.json").write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
        wc = sum(words(p["text"]) for p in data["provisions"])
        print(f"{slug}: {len(data['provisions'])} provisions, {wc} words")


if __name__ == "__main__":
    main(sys.argv[1:])
