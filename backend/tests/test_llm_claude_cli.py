import json
import os

import pytest

from app.llm import LLMError, get_provider, parse_json_object, settings, base
from app.llm.claude_cli import ClaudeCLIProvider


class FakeProc:
    def __init__(self, out=b"", err=b"", rc=0, lines=None):
        self.out, self.err, self.returncode = out, err, rc
        self.stdin_data = None
        self._lines = lines
        outer = self

        class R:
            def __init__(s, data):
                s.data = data

            async def readline(s):
                return s.data.pop(0) if s.data else b""

            async def read(s):
                return b"".join(s.data)

        self.stdout = R(list(lines or []))
        self.stderr = R([err])

        class W:
            def write(s, d):
                outer.stdin_data = d

            async def drain(s):
                pass

            def close(s):
                pass

        self.stdin = W()

    async def communicate(self, data):
        self.stdin_data = data
        return self.out, self.err

    async def wait(self):
        return self.returncode

    def kill(self):
        pass


@pytest.fixture(autouse=True)
def env(tmp_path, monkeypatch):
    monkeypatch.setenv("LLM_CACHE", "0")
    monkeypatch.setenv("LLM_PROVIDER", "claude_cli")
    monkeypatch.setenv("CLAUDE_CLI_CWD", str(tmp_path / "cwd"))
    settings.get_settings.cache_clear()
    base._cache = None
    yield
    settings.get_settings.cache_clear()
    base._cache = None


def patch_spawn(monkeypatch, proc, captured):
    async def fake(*argv, **kw):
        captured["argv"], captured["kw"] = argv, kw
        return proc

    monkeypatch.setattr("asyncio.create_subprocess_exec", fake)


OK = {"type": "result", "is_error": False, "result": '{"x": 1}', "total_cost_usd": 0.0123,
      "usage": {"input_tokens": 5, "output_tokens": 7, "cache_read_input_tokens": 10, "cache_creation_input_tokens": 100},
      "modelUsage": {"claude-sonnet-5-5": {}}}


async def test_complete_argv_and_parse(monkeypatch, tmp_path):
    cap = {}
    patch_spawn(monkeypatch, FakeProc(out=json.dumps(OK).encode()), cap)
    p = get_provider("claude_cli", "sonnet")
    r = await p.complete([{"role": "system", "content": "SYS"}, {"role": "user", "content": "hello $(rm -rf /)"}],
                         json_mode=True)
    argv = list(cap["argv"])
    assert argv[:2] == [p.cli, "-p"]
    for flag in ("--no-session-persistence", "--strict-mcp-config"):
        assert flag in argv
    assert "--bare" not in argv
    assert argv[argv.index("--model") + 1] == "sonnet"
    assert argv[argv.index("--tools") + 1] == ""
    assert argv[argv.index("--output-format") + 1] == "json"
    assert "SYS" in argv[argv.index("--system-prompt") + 1] and "JSON" in argv[argv.index("--system-prompt") + 1]
    assert "hello" not in " ".join(argv)  # prompt goes via stdin only
    assert r.text == '{"x": 1}' and parse_json_object(r.text) == {"x": 1}
    assert r.model == "claude-sonnet-5-5" and r.output_tokens == 7 and r.input_tokens == 115
    assert r.cost_usd == 0.0123 and not r.cached
    assert (tmp_path / "cwd").is_dir() and cap["kw"]["cwd"] == str(tmp_path / "cwd")


async def test_is_error_retryable_and_not(monkeypatch):
    cap = {}
    p = get_provider("claude_cli")
    bad = dict(OK, is_error=True, result="Credit balance too low")
    patch_spawn(monkeypatch, FakeProc(out=json.dumps(bad).encode()), cap)
    with pytest.raises(LLMError) as ei:
        await p._complete([{"role": "user", "content": "x"}], temperature=0, max_tokens=1, json_mode=False)
    assert not ei.value.retryable
    bad = dict(OK, is_error=True, result="API Error: 529 overloaded")
    patch_spawn(monkeypatch, FakeProc(out=json.dumps(bad).encode()), cap)
    with pytest.raises(LLMError) as ei:
        await p._complete([{"role": "user", "content": "x"}], temperature=0, max_tokens=1, json_mode=False)
    assert ei.value.retryable


async def test_nonzero_exit(monkeypatch):
    patch_spawn(monkeypatch, FakeProc(out=b"", err=b"boom", rc=1), {})
    with pytest.raises(LLMError, match="exited 1"):
        await get_provider("claude_cli")._complete([{"role": "user", "content": "x"}], temperature=0,
                                                   max_tokens=1, json_mode=False)


async def test_stream(monkeypatch):
    def ev(t):
        return (json.dumps({"type": "stream_event", "event": {"type": "content_block_delta",
                                                               "delta": {"type": "text_delta", "text": t}}}) + "\n").encode()

    lines = [b'{"type":"system"}\n', ev("Hel"), ev("lo"), (json.dumps(dict(OK, result="Hello")) + "\n").encode()]
    cap = {}
    patch_spawn(monkeypatch, FakeProc(lines=lines), cap)
    out = [x async for x in get_provider("claude_cli").stream([{"role": "user", "content": "x"}])]
    assert out[:2] == ["Hel", "lo"] and out[-1].text == "Hello" and out[-1].model == "claude-sonnet-5-5"
    argv = list(cap["argv"])
    assert "--include-partial-messages" in argv and "--verbose" in argv
    assert argv[argv.index("--output-format") + 1] == "stream-json"


def test_unknown_provider():
    with pytest.raises(LLMError, match="valid"):
        get_provider("nope")


def test_nvidia_requires_key(monkeypatch):
    monkeypatch.setenv("NVIDIA_API_KEY", "")
    settings.get_settings.cache_clear()
    with pytest.raises(LLMError, match="NVIDIA_API_KEY"):
        get_provider("nvidia", "x")


live = pytest.mark.skipif(os.environ.get("LIVE_LLM") != "1", reason="set LIVE_LLM=1")


@pytest.mark.live
@live
async def test_live_claude_cli(tmp_path, monkeypatch):
    monkeypatch.undo()  # real subprocess
    monkeypatch.setenv("LLM_CACHE", "1")
    monkeypatch.setenv("LLM_CACHE_PATH", str(tmp_path / "live.sqlite"))
    settings.get_settings.cache_clear()
    base._cache = None
    p = get_provider("claude_cli", "sonnet")
    msgs = [{"role": "system", "content": "You are terse."},
            {"role": "user", "content": 'Return a JSON object with key "answer" equal to 2+2 and key "lang" equal to "en".'}]
    r1 = await p.complete(msgs, json_mode=True)
    print(f"\nLIVE complete: {r1.latency_ms}ms in={r1.input_tokens} out={r1.output_tokens} "
          f"cost={r1.cost_usd} model={r1.model} text={r1.text!r}")
    assert parse_json_object(r1.text)["answer"] == 4 and not r1.cached
    r2 = await p.complete(msgs, json_mode=True)
    print(f"LIVE cached: {r2.latency_ms}ms cached={r2.cached}")
    assert r2.cached and r2.text == r1.text

    smsgs = [{"role": "user", "content": "Count from 1 to 5 separated by spaces, nothing else."}]
    items = [x async for x in p.stream(smsgs)]
    deltas, final = items[:-1], items[-1]
    print(f"LIVE stream: {len(deltas)} deltas, {final.latency_ms}ms in={final.input_tokens} "
          f"out={final.output_tokens} cost={final.cost_usd} text={final.text!r}")
    assert deltas and "".join(deltas) == final.text and "5" in final.text
    items2 = [x async for x in p.stream(smsgs)]
    print(f"LIVE stream cached: {items2[-1].cached} {items2[-1].latency_ms}ms")
    assert items2[-1].cached and items2[0] == final.text
