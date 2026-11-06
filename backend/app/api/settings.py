"""Pick the model behind the checker: a Claude or ChatGPT subscription, an API key, or a local model."""
from __future__ import annotations

import asyncio
import time
from typing import Any

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from app.llm import LLMError, get_provider
from app.llm import settings_store as store
from app.llm.settings import get_settings

router = APIRouter(prefix="/api/settings/llm", tags=["settings"])


class LLMUpdate(BaseModel):
    target: str
    api_key: str | None = None
    model: str | None = None
    activate: bool = False


def reset(request: Request) -> None:
    """Drop cached settings and the pipeline's provider so the next call uses the new choice."""
    get_settings.cache_clear()
    pipeline = getattr(request.app.state, "pipeline", None)
    if pipeline is not None and hasattr(pipeline, "_provider"):
        pipeline._provider = None


@router.get("", summary="Connection options and the one in use")
async def read() -> dict[str, Any]:
    return store.describe(get_settings())


@router.put("", summary="Save a key or model, optionally switch to that option")
async def update(body: LLMUpdate, request: Request) -> dict[str, Any]:
    spec = store.BY_ID.get(body.target)
    if spec is None:
        raise HTTPException(404, f"unknown option {body.target!r}")
    changes: dict[str, str] = {}
    if body.api_key is not None:
        if not spec.key_field:
            raise HTTPException(422, f"{spec.label} does not take an API key")
        changes[spec.key_field] = body.api_key
    if body.model is not None:
        changes[spec.model_field] = body.model
    if body.activate:
        changes["llm_provider"] = spec.id
    store.save_overrides(changes)
    reset(request)
    return store.describe(get_settings())


@router.post("/test/{target}", summary="Send a tiny prompt through one option (bypasses the cache)")
async def test(target: str) -> dict[str, Any]:
    spec = store.BY_ID.get(target)
    if spec is None:
        raise HTTPException(404, f"unknown option {target!r}")
    s = get_settings()
    if spec.key_field and not getattr(s, spec.key_field):
        return {"ok": False, "error": "No API key saved yet.", "latency_s": 0}
    model = store.model_of(s, spec)
    if spec.kind == "api_key" and not model:
        return {"ok": False, "error": "Pick a model first.", "latency_s": 0}
    t0 = time.perf_counter()
    try:
        provider = get_provider(target, model or None)
        res = await asyncio.wait_for(provider._complete(
            [{"role": "user", "content": 'Reply with the JSON {"ok": true}.'}],
            temperature=0.0, max_tokens=50, json_mode=True), timeout=90)
    except LLMError as e:
        return {"ok": False, "error": str(e)[:300], "latency_s": round(time.perf_counter() - t0, 2)}
    except TimeoutError:
        return {"ok": False, "error": "No answer within 90 s.", "latency_s": round(time.perf_counter() - t0, 2)}
    return {"ok": True, "model": res.model, "latency_s": round(time.perf_counter() - t0, 2)}
