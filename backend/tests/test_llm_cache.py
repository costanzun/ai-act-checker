import pytest

from app.llm import cache as cache_mod
from app.llm import base, settings
from app.llm.base import LLMError, LLMProvider, LLMResult


class Fake(LLMProvider):
    name = "fake"
    model = "m1"

    def __init__(self):
        self.calls = 0
        self.fail_first = 0

    async def _complete(self, messages, *, temperature, max_tokens, json_mode):
        self.calls += 1
        if self.fail_first:
            self.fail_first -= 1
            raise LLMError("overloaded", retryable=True)
        return LLMResult("hello", "m1-resolved", "fake", 3, 4, 0.01, 5)

    async def _stream(self, messages, *, temperature, max_tokens):
        self.calls += 1
        yield "he"
        yield "llo"
        yield LLMResult("hello", "m1-resolved", "fake", 3, 4, 0.01, 5)


@pytest.fixture
def tmp_cache(tmp_path, monkeypatch):
    monkeypatch.setenv("LLM_CACHE", "1")
    monkeypatch.setenv("LLM_CACHE_PATH", str(tmp_path / "c.sqlite"))
    settings.get_settings.cache_clear()
    base._cache = None
    yield tmp_path / "c.sqlite"
    base._cache = None
    settings.get_settings.cache_clear()


def test_key_differs():
    k = cache_mod.make_key
    m = [{"role": "user", "content": "x"}]
    assert k("p", "m", m, 0.0, 10, False) == k("p", "m", m, 0.0, 10, False)
    assert k("p", "m", m, 0.0, 10, False) != k("p", "m", m, 0.1, 10, False)
    assert k("p", "m", m, 0.0, 10, False) != k("p", "m", m, 0.0, 10, True)
    assert k("p", "m", m, 0.0, 10, False) != k("q", "m", m, 0.0, 10, False)


async def test_complete_cached(tmp_cache):
    p, msgs = Fake(), [{"role": "user", "content": "hi"}]
    r1 = await p.complete(msgs)
    r2 = await p.complete(msgs)
    assert p.calls == 1 and not r1.cached and r2.cached
    assert (r2.text, r2.model, r2.input_tokens, r2.output_tokens, r2.cost_usd) == ("hello", "m1-resolved", 3, 4, 0.01)
    assert tmp_cache.exists()
    r3 = await p.complete(msgs, temperature=0.5)
    assert p.calls == 2 and not r3.cached


async def test_stream_cached_replayed_as_one_delta(tmp_cache):
    p, msgs = Fake(), [{"role": "user", "content": "s"}]
    first = [x async for x in p.stream(msgs)]
    assert first[:2] == ["he", "llo"] and isinstance(first[-1], LLMResult)
    second = [x async for x in p.stream(msgs)]
    assert second[0] == "hello" and second[-1].cached and len(second) == 2
    assert p.calls == 1


async def test_cache_disabled(tmp_cache, monkeypatch):
    monkeypatch.setenv("LLM_CACHE", "0")
    settings.get_settings.cache_clear()
    p, msgs = Fake(), [{"role": "user", "content": "hi"}]
    await p.complete(msgs)
    await p.complete(msgs)
    assert p.calls == 2


async def test_retry_transient(tmp_cache, monkeypatch):
    from app.llm import limits
    slept = []

    async def fake_sleep(d):
        slept.append(d)

    monkeypatch.setattr(limits.asyncio, "sleep", fake_sleep)
    p = Fake()
    p.fail_first = 2
    r = await p.complete([{"role": "user", "content": "r"}])
    assert r.text == "hello" and p.calls == 3 and slept == [1, 3]
    p.fail_first = 5
    with pytest.raises(LLMError):
        await p.complete([{"role": "user", "content": "r2"}])
