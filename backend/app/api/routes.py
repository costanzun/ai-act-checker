"""HTTP routes (CONTRACTS §7)."""

from __future__ import annotations

import json
import logging
import os
from typing import Any

from fastapi import APIRouter, HTTPException, Query, Request
from sse_starlette.sse import EventSourceResponse

from app import engine
from app.examples import examples_for
from app.llm import LLMError
from app.pipeline import Pipeline
from app.schemas import AssessRequest, MetaResponse

log = logging.getLogger("ai_act.api")
router = APIRouter()


def _pipeline(request: Request) -> Pipeline:
    return request.app.state.pipeline


@router.get("/health")
async def health(request: Request) -> dict[str, Any]:
    p = _pipeline(request)
    try:
        prov = p.provider_for(AssessRequest(description="x" * 20))
        provider, model = prov.name, prov.model
    except LLMError as exc:
        provider, model = f"unavailable ({exc})", ""
    return {"status": "ok", "provider": provider, "model": model, "corpus_loaded": p.store.exists("art:6.2")}


@router.get("/api/meta", response_model=MetaResponse)
async def meta(request: Request) -> MetaResponse:
    p = _pipeline(request)
    m = p.store.meta("en")
    try:
        prov = p.provider_for(AssessRequest(description="x" * 20))
        provider, model = prov.name, prov.model
    except LLMError as exc:
        provider, model = "unavailable", str(exc)
    return MetaResponse(
        amending_acts=[
            {k: str(v) for k, v in (a.model_dump() if hasattr(a, "model_dump") else dict(a)).items() if v is not None}
            for a in (getattr(m, "amending_acts", None) or [])
        ],
        provider=provider,
        model=model,
        timeline=engine.timeline(),
    )


@router.get("/api/examples")
async def examples(lang: str = Query("en")) -> dict[str, Any]:
    return {"examples": examples_for(lang)}


@router.get("/api/law/search")
async def law_search(
    request: Request,
    q: str = Query(..., min_length=2),
    lang: str = Query("en"),
    k: int = Query(8, ge=1, le=30),
    guidance: bool = Query(False, description="Also search non-binding Commission guidance"),
) -> dict[str, Any]:
    p = _pipeline(request)
    r = p.retriever
    if r is None:
        raise HTTPException(503, "retrieval index not available")
    return {"hits": r.search(q, lang=lang, k=k, binding=None if guidance else True)}


@router.get("/api/law/{pid}")
async def law(request: Request, pid: str, lang: str = Query("en")) -> dict[str, Any]:
    p = _pipeline(request)
    lang = lang if lang in ("en", "it") else "en"
    prov = p.store.get(pid, lang)
    if prov is None:
        raise HTTPException(404, f"unknown provision id: {pid}")
    breadcrumb: list[dict[str, str]] = []
    cur: Any = prov
    guard = 0
    while cur is not None and guard < 8:
        breadcrumb.insert(0, {"id": cur.id, "label": cur.label})
        cur = p.store.get(cur.parent_id, lang) if getattr(cur, "parent_id", None) else None
        guard += 1
    children = [c.model_dump() for c in (p.store.get(cid, lang) for cid in prov.children) if c is not None]
    return {
        "provision": prov.model_dump(),
        "full_text": p.store.full_text(pid, lang),
        "breadcrumb": breadcrumb,
        "children": children,
        "eurlex_url": p.store.eurlex_url(pid, lang),
    }


@router.post("/api/assess")
async def assess(request: Request, body: AssessRequest) -> EventSourceResponse:
    p = _pipeline(request)
    if os.getenv("ALLOW_CLIENT_MODEL", "0") != "1":
        body.provider = None  # the server decides which model pays for the call
        body.model = None

    async def gen():
        try:
            async for name, payload in p.run(body):
                if await request.is_disconnected():
                    log.info("client disconnected; stopping assessment")
                    return
                yield {"event": name, "data": json.dumps(payload, ensure_ascii=False)}
        except LLMError as exc:
            log.error("LLM error: %s", exc)
            yield {
                "event": "error",
                "data": json.dumps(
                    {
                        "code": "llm_unavailable",
                        "message": {
                            "en": "The language model is not available right now (rate limit, network or configuration). Please try again in a moment.",
                            "it": "Il modello linguistico non è disponibile al momento (limite di utilizzo, rete o configurazione). Riprova tra poco.",
                        },
                    },
                    ensure_ascii=False,
                ),
            }
        except Exception as exc:  # pragma: no cover - defensive
            log.exception("assessment failed")
            yield {
                "event": "error",
                "data": json.dumps(
                    {
                        "code": "internal",
                        "message": {"en": f"Unexpected error: {type(exc).__name__}", "it": f"Errore inatteso: {type(exc).__name__}"},
                    },
                    ensure_ascii=False,
                ),
            }

    return EventSourceResponse(gen(), ping=15)
