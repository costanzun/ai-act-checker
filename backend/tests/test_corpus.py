"""Tests for the legal corpus (data/corpus/{en,it}.json) and CorpusStore."""

from __future__ import annotations

import pytest

from app.corpus.parser import make_label, token_of
from app.corpus.store import CorpusStore


@pytest.fixture(scope="module")
def store() -> CorpusStore:
    return CorpusStore()


def ids(store: CorpusStore, lang: str) -> set[str]:
    return {p.id for p in store.iter(lang)}


# --- counts / structure ---------------------------------------------------------


@pytest.mark.parametrize("lang", ["en", "it"])
def test_counts(store: CorpusStore, lang: str) -> None:
    c = store.meta(lang).counts
    # 113 numbered articles + 4a, 60a, 75a-75d inserted by the Digital Omnibus
    assert c["articles"] == 119
    assert c["annexes"] == 14  # I-XIII + XIV added by the Digital Omnibus
    assert c["recitals"] == 180
    assert c["provisions"] == sum(1 for _ in store.iter(lang))
    assert c["provisions"] > 1500
    for t, key in (("article", "articles"), ("annex", "annexes"), ("recital", "recitals")):
        assert sum(1 for _ in store.iter(lang, {t})) == c[key]


def test_numbered_articles_1_to_113(store: CorpusStore) -> None:
    for n in range(1, 114):
        assert store.exists(f"art:{n}"), n
    for n in ("4a", "60a", "75a", "75b", "75c", "75d"):
        assert store.exists(f"art:{n}")


def test_ids_identical_en_it(store: CorpusStore) -> None:
    en, it = ids(store, "en"), ids(store, "it")
    assert en == it, (sorted(en - it)[:10], sorted(it - en)[:10])


@pytest.mark.parametrize("lang", ["en", "it"])
def test_integrity(store: CorpusStore, lang: str) -> None:
    provs = list(store.iter(lang))
    by_id = {p.id: p for p in provs}
    assert len(by_id) == len(provs)
    orders = [p.order for p in provs]
    assert orders == sorted(orders) and len(set(orders)) == len(orders)
    for p in provs:
        if p.parent_id:
            assert p.parent_id in by_id
            assert p.id in by_id[p.parent_id].children
        for c in p.children:
            assert by_id[c].parent_id == p.id
        deleted = p.amendment is not None and p.amendment.kind == "deleted"
        assert deleted or p.text, p.id
        assert "▼" not in p.text and "►" not in p.text and "◄" not in p.text
        assert " " * 2 not in p.text


def test_chapters_and_sections(store: CorpusStore) -> None:
    p = store.get("art:6.2")
    assert p and (p.chapter, p.chapter_title) == ("III", "High-risk AI systems")
    assert (p.section, p.section_title) == ("1", "Classification of AI systems as high-risk")
    assert p.title == "Classification rules for high-risk AI systems"
    a5 = store.get("art:5")
    assert a5 and a5.chapter == "II" and a5.section is None
    assert store.get("art:4a").chapter == "I"  # type: ignore[union-attr]
    it6 = store.get("art:6.2", "it")
    assert it6 and it6.chapter == "III"


# --- spot checks (EN) -------------------------------------------------------------


def test_art_6_2(store: CorpusStore) -> None:
    p = store.get("art:6.2")
    assert p and p.type == "paragraph" and p.parent_id == "art:6"
    assert "Annex III shall be considered to be high-risk" in p.text


def test_art_5(store: CorpusStore) -> None:
    f = store.get("art:5.1.f")
    assert f and f.type == "point"
    low = f.text.lower()
    assert "emotions" in low and "workplace" in low and "education" in low
    for pid in ("art:5.1.ba", "art:5.1.bb"):
        p = store.get(pid)
        assert p and p.amendment and p.amendment.kind == "inserted"
        assert p.amendment.marker == "M1" and p.amendment.by == "32026R1744"
    para = store.get("art:5.1a")
    assert para and para.type == "paragraph"
    assert para.amendment and para.amendment.kind == "inserted"
    assert store.get("art:5.1.h.i") is not None
    b = store.get("art:5.1.b")
    assert b and b.amendment is None
    assert store.get("art:5.1.c") and store.get("art:5.1.c").amendment is None  # type: ignore[union-attr]
    # text that follows the points of a paragraph is kept in order
    p51 = store.get("art:5.1")
    assert p51 and p51.text_after and "Point (h)" in p51.text_after


def test_art_113(store: CorpusStore) -> None:
    full = store.full_text("art:113")
    assert "2 December 2027" in full and "2 August 2028" in full
    assert "It shall apply from 2 August 2026" in full
    c = store.get("art:113.c")
    assert c and c.amendment and c.amendment.kind == "replaced"
    assert any(
        d.amendment and d.amendment.marker == "M1"
        for d in (store.get(x) for x in store.get("art:113.c").children)  # type: ignore[union-attr]
        if d
    )
    assert "2 December 2027" in store.get("art:113.c.i").text  # type: ignore[union-attr]
    assert "2 August 2028" in store.get("art:113.c.ii").text  # type: ignore[union-attr]
    assert store.get("art:113.b").amendment is None  # type: ignore[union-attr]


def test_annex_points(store: CorpusStore) -> None:
    a = store.get("annex:III.4.a")
    assert a and ("recruitment" in a.text or "selection" in a.text)
    c = store.get("annex:III.1.c")
    assert c and "emotion recognition" in c.text
    p = store.get("annex:I.A.11")
    assert p and "2017/745" in p.text and "medical devices" in p.text
    assert store.get("annex:III.8.b") is not None
    assert store.get("annex:XIII.a") is not None
    assert store.get("annex:VIII.B.1") is not None
    assert store.get("annex:XI.1.1.a") is not None


def test_deleted_nodes_keep_id(store: CorpusStore) -> None:
    deleted = {p.id for p in store.iter("en") if p.amendment and p.amendment.kind == "deleted"}
    assert {"art:10.5", "annex:I.A.1", "annex:VIII.B.7", "annex:VIII.B.9"} <= deleted
    p = store.get("art:10.5")
    assert p and p.text == "" and p.type == "paragraph"
    assert "Art. 10(5)" == p.label
    assert "5." not in [ln.split(" ")[0] for ln in store.full_text("art:10").splitlines()]


def test_other_provisions_exist(store: CorpusStore) -> None:
    for pid in ("rec:57", "art:50.1", "art:26.7", "art:27", "art:4", "art:53.1.a", "art:3.1", "art:43.1.a-2"):
        assert store.exists(pid), pid
    assert "recruitment" in store.get("rec:57").text  # type: ignore[union-attr]
    assert store.get("rec:57").type == "recital"  # type: ignore[union-attr]
    assert "emotion" in store.full_text("art:50").lower()
    assert store.get("nonsense:1") is None and not store.exists("nonsense:1")


def test_footnote_and_marker_artefacts_removed(store: CorpusStore) -> None:
    t = store.get("art:40.2").text  # type: ignore[union-attr]
    assert "of the Council and without undue delay" in t  # footnote reference "(1)" dropped
    assert store.get("art:51.2").text.endswith("10²⁵.")  # type: ignore[union-attr]
    for p in store.iter("en"):
        assert "()" not in p.text and "(*" not in p.text, p.id


# --- Italian -------------------------------------------------------------------------


def test_italian(store: CorpusStore) -> None:
    p = store.get("art:6.2", "it")
    assert p and "allegato iii" in p.text.lower()
    assert p.label == "Art. 6, par. 2"
    assert store.label("art:6.3.a", "it") == "Art. 6, par. 3, lett. a)"
    assert store.label("art:5.1.h.i", "it") == "Art. 5, par. 1, lett. h), punto i)"
    assert store.label("annex:I.A.11", "it") == "Allegato I, sezione A, punto 11"
    assert store.label("annex:III.4.a", "it") == "Allegato III, punto 4, lett. a)"
    assert store.label("rec:57", "it") == "Considerando 57"
    assert store.label("annex:III", "it") == "Allegato III"
    assert store.get("art:5.1.ba", "it") is not None  # "b bis)" in the Italian text
    assert store.get("art:4a", "it").title  # type: ignore[union-attr]


def test_english_labels(store: CorpusStore) -> None:
    assert store.label("art:6") == "Art. 6"
    assert store.label("art:6.2") == "Art. 6(2)"
    assert store.label("art:6.3.a") == "Art. 6(3)(a)"
    assert store.label("art:5.1.h.i") == "Art. 5(1)(h)(i)"
    assert store.label("art:5.1a") == "Art. 5(1a)"
    assert store.label("art:5.1.ba") == "Art. 5(1)(ba)"
    assert store.label("annex:III") == "Annex III"
    assert store.label("annex:III.4") == "Annex III, point 4"
    assert store.label("annex:III.4.a") == "Annex III, point 4(a)"
    assert store.label("annex:I.A.11") == "Annex I, Section A, point 11"
    assert store.label("annex:VII.3.1.a") == "Annex VII, point 3.1(a)"
    assert store.label("rec:57") == "Recital 57"
    assert store.label("art:3.1") == "Art. 3, point (1)"
    assert store.label("unknown") == "unknown"


# --- store API --------------------------------------------------------------------------


def test_full_text_assembly(store: CorpusStore) -> None:
    ft = store.full_text("art:6.3")
    assert ft.startswith("By derogation from paragraph 2")
    assert "\n(a) the AI system is intended to perform a narrow procedural task" in ft
    assert ft.splitlines()[-1].startswith("Notwithstanding the first subparagraph")
    art = store.full_text("art:5")
    assert art.splitlines()[0] == "Prohibited AI practices"
    assert "\n1. The following AI practices shall be prohibited:" in art
    assert "\n    (i) detrimental or unfavourable treatment" in art
    assert "(ba) the placing on the market" in art
    assert store.full_text("art:99999") == ""
    # a deleted paragraph does not leak into the article text
    assert "\n5. " not in store.full_text("art:10")


def test_iter_and_filters(store: CorpusStore) -> None:
    recs = list(store.iter("en", {"recital"}))
    assert len(recs) == 180 and recs[0].id == "rec:1" and recs[-1].id == "rec:180"
    arts = [p.id for p in store.iter("it", {"article"})]
    assert arts[0] == "art:1" and "art:4a" in arts
    first_art = next(store.iter("en", {"article"}))
    assert first_art.order > recs[-1].order  # preamble precedes enacting terms


def test_meta(store: CorpusStore) -> None:
    m = store.meta("en")
    assert m.celex == "02024R1689-20260727" and m.language == "en"
    assert m.consolidated_as_of == "2026-07-27"
    assert m.amending_acts[0].celex == "32026R1744" and m.amending_acts[0].marker == "M1"
    assert store.meta("it").language == "it"
    with pytest.raises(ValueError):
        store.meta("fr")


def test_eurlex_url(store: CorpusStore) -> None:
    u = store.eurlex_url("art:6.2")
    assert u.startswith("https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:02024R1689-20260727")
    assert u.endswith("#art_6")
    assert "/IT/" in store.eurlex_url("annex:III", "it") and store.eurlex_url("annex:III", "it").endswith("#anx_III")
    r = store.eurlex_url("rec:57")
    assert "CELEX:32024R1689" in r and r.endswith("#rct_57")


def test_breadcrumb_and_children(store: CorpusStore) -> None:
    assert [p.id for p in store.breadcrumb("art:5.1.h.i")] == ["art:5", "art:5.1", "art:5.1.h", "art:5.1.h.i"]
    assert [p.id for p in store.children("annex:III.1")] == ["annex:III.1.a", "annex:III.1.b", "annex:III.1.c"]


# --- parser helpers -------------------------------------------------------------------------


def test_token_of() -> None:
    assert token_of("(a) ") == "a"
    assert token_of("(ba) ") == "ba"
    assert token_of("1a.  ") == "1a"
    assert token_of("14 bis) ") == "14a"
    assert token_of("b bis) ") == "ba"
    assert token_of("3.1.") == "3.1"
    assert token_of("«68) ") == "68"
    assert token_of("—") is None


def test_make_label() -> None:
    assert make_label([("art", "113"), ("pt", "c"), ("pt", "ii")], "en") == "Art. 113, point (c)(ii)"
    assert make_label([("annex", "VIII"), ("sec", "B"), ("apt", "7")], "it") == "Allegato VIII, sezione B, punto 7"
