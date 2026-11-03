import io
import json
from pathlib import Path
from types import SimpleNamespace

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pypdf import PdfReader

from app.api.export import router
from app.corpus.store import CorpusStore
from app.export.markdown import render_markdown
from app.export.pdf import render_pdf
from app.schemas import Assessment

HERE = Path(__file__).parent
STORE = CorpusStore(HERE.parent.parent / "data" / "corpus")
RAW = json.loads((HERE / "fixtures" / "assessment_cv_screening.json").read_text(encoding="utf-8"))


def load(lang="en") -> Assessment:
    return Assessment.model_validate({**RAW, "language": lang})


def test_markdown_en():
    a = load()
    md = render_markdown(a, STORE)
    assert "High-risk AI system" in md
    assert "Cited provisions" in md and "Not legal advice" in md
    assert "[[" not in md
    ids = {i for f in a.classification.findings for i in f.citations}
    for i in ids:
        assert STORE.label(i, "en") in md
    assert "[Art. 6(2)](https://eur-lex.europa.eu" in md
    assert "- [ ] " in md
    assert md.count("### Art. 6(2)") == 1  # appendix has each provision once
    assert "> We are a 200-person" in md


def test_markdown_it():
    md = render_markdown(load("it"), STORE)
    for h in ("## Motivazione", "## Riscontri", "## Checklist di conformità", "## Disposizioni citate"):
        assert h in md
    assert "Sistema di IA ad alto rischio" in md
    assert "Art. 6, par. 2" in md
    assert "[[" not in md
    assert "novembre 2026" in md


def test_appendix_capped():
    md = render_markdown(load(), STORE)
    app = md.split("## Cited provisions", 1)[1]
    for block in app.split("### ")[1:]:
        assert len(block) < 1500 + 400


@pytest.mark.parametrize("lang,title,label", [("en", "EU AI Act assessment", "Art. 6(2)"), ("it", "Valutazione AI Act UE", "Art. 6, par. 2")])
def test_pdf(lang, title, label):
    data = render_pdf(load(lang), STORE)
    assert data[:4] == b"%PDF"
    r = PdfReader(io.BytesIO(data))
    assert len(r.pages) >= 2
    text = "\n".join(p.extract_text() for p in r.pages)
    assert title in text
    assert label in text
    assert "[[" not in text
    links = [an for p in r.pages for an in (p.get("/Annots") or [])]
    assert any("eur-lex" in str(an.get_object().get("/A", {}).get("/URI", "")) for an in links)


@pytest.fixture()
def client():
    app = FastAPI()
    app.state.pipeline = SimpleNamespace(store=STORE)
    app.include_router(router)
    return TestClient(app)


def test_api_markdown(client):
    r = client.post("/api/export/markdown", json={"assessment": RAW})
    assert r.status_code == 200
    assert r.headers["content-type"].startswith("text/markdown")
    assert r.headers["content-disposition"] == f'attachment; filename="ai-act-assessment-{RAW["id"][:8]}.md"'
    assert "High-risk AI system" in r.text


def test_api_pdf(client):
    r = client.post("/api/export/pdf", json={"assessment": RAW})
    assert r.status_code == 200
    assert r.headers["content-type"] == "application/pdf"
    assert r.headers["content-disposition"].endswith('.pdf"')
    assert r.content[:4] == b"%PDF"


def test_api_invalid(client):
    assert client.post("/api/export/pdf", json={"assessment": {}}).status_code == 422
