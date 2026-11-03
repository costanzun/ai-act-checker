"""FastAPI application entry point (port 8101 by default)."""

from __future__ import annotations

import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

ROOT = Path(__file__).resolve().parents[2]
load_dotenv(ROOT / ".env")
load_dotenv(ROOT / "backend" / ".env")

logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"), format="%(asctime)s %(levelname)s %(name)s: %(message)s")
log = logging.getLogger("ai_act")


@asynccontextmanager
async def lifespan(app: FastAPI):
    from app.corpus.store import CorpusStore
    from app.pipeline import Pipeline

    store = CorpusStore(ROOT / "data" / "corpus")
    app.state.pipeline = Pipeline(store)
    if not store.exists("art:6.2"):
        log.error("Corpus not found in data/corpus. Run: backend/.venv/bin/python scripts/build_corpus.py")
    else:
        log.info("Corpus loaded (law as of %s)", getattr(store.meta("en"), "consolidated_as_of", "?"))
    if os.getenv("WARM_RETRIEVER", "1") == "1":
        try:
            _ = app.state.pipeline.retriever  # loads embedder/reranker lazily on first use
        except Exception as exc:  # pragma: no cover
            log.warning("retriever warm-up skipped: %s", exc)
    yield


app = FastAPI(title="EU AI Act Checker API", version="0.1.0", lifespan=lifespan)

origins = [o.strip() for o in os.getenv("CORS_ORIGINS", "http://localhost:3101").split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

from app.api.routes import router  # noqa: E402

app.include_router(router)

try:  # export routes are added by a separate module; optional until present
    from app.api.export import router as export_router  # noqa: E402

    app.include_router(export_router)
except ImportError:  # pragma: no cover
    log.warning("export routes not available yet")
