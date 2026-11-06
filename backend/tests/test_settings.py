"""Model picker: saved overrides, masked keys, switching provider, per-provider models, Codex wrapper.

No test runs a real CLI or calls a real API.
"""
from __future__ import annotations

import stat
from pathlib import Path
from types import SimpleNamespace

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.settings import router
from app.llm import LLMError, get_provider, settings
from app.llm import settings_store as store
from app.llm.codex_cli import build_command, build_stdin, check_exit
from app.llm.openai_compat import OpenAICompatProvider

FAKE_KEY = "sk-test-1234567890abcd"  # not a real key


@pytest.fixture
def env(monkeypatch, tmp_path):
    for k in ("LLM_PROVIDER", "LLM_MODEL", "CLAUDE_CLI_MODEL", "ANTHROPIC_API_KEY", "OPENAI_API_KEY",
              "NVIDIA_API_KEY", "OPENAI_MODEL", "ANTHROPIC_MODEL"):
        monkeypatch.setenv(k, "")
    monkeypatch.setenv("LLM_PROVIDER", "claude_cli")
    monkeypatch.setenv("CODEX_CLI_PATH", str(tmp_path / "no-codex-here"))
    settings.get_settings.cache_clear()
    return store.FILE  # conftest points it at a temp file


@pytest.fixture
def client(env):
    app = FastAPI()
    app.state.pipeline = SimpleNamespace(_provider=object())
    app.include_router(router)
    c = TestClient(app)
    c.pipeline = app.state.pipeline
    return c


def opt(body: dict, pid: str) -> dict:
    return next(p for p in body["providers"] if p["id"] == pid)


def test_lists_every_option(client):
    body = client.get("/api/settings/llm").json()
    ids = [p["id"] for p in body["providers"]]
    assert ids == ["claude_cli", "codex_cli", "anthropic_api", "openai_api", "nvidia", "local_mlx"]
    assert body["active"] == "claude_cli" and opt(body, "claude_cli")["active"]
    assert sum(p["active"] for p in body["providers"]) == 1
    assert opt(body, "claude_cli")["model"] == "sonnet"
    assert "claude-opus-5-5" in opt(body, "anthropic_api")["suggestions"]


def test_codex_missing_is_reported_without_running_it(client):
    p = opt(client.get("/api/settings/llm").json(), "codex_cli")
    assert p["status"] == "Codex CLI is not installed" and not p["ready"]
    with pytest.raises(LLMError, match="codex login"):
        get_provider("codex_cli")
    r = client.post("/api/settings/llm/test/codex_cli").json()
    assert r["ok"] is False and "not found" in r["error"]


def test_key_is_masked_saved_privately_and_switches(client, env: Path):
    client.pipeline._provider = object()
    r = client.put("/api/settings/llm", json={"target": "openai_api", "api_key": FAKE_KEY,
                                              "model": "some-model", "activate": True})
    body = r.json()
    p = opt(body, "openai_api")
    assert body["active"] == "openai_api" and p["active"] and p["ready"] and p["model"] == "some-model"
    assert p["key_hint"] == "sk-…abcd" and "1234567890" not in r.text
    assert stat.S_IMODE(env.stat().st_mode) == 0o600
    assert settings.get_settings().openai_api_key == FAKE_KEY
    assert client.pipeline._provider is None  # the pipeline picks up the new provider
    prov = get_provider()
    assert prov.name == "openai_api" and prov.base_url == "https://api.openai.com/v1" and prov.model == "some-model"
    # removing the key, then switching back
    body = client.put("/api/settings/llm", json={"target": "openai_api", "api_key": ""}).json()
    assert not opt(body, "openai_api")["has_key"]
    body = client.put("/api/settings/llm", json={"target": "claude_cli", "activate": True}).json()
    assert body["active"] == "claude_cli"


def test_models_are_per_provider(client):
    client.put("/api/settings/llm", json={"target": "claude_cli", "model": "opus"})
    client.put("/api/settings/llm", json={"target": "anthropic_api", "model": "claude-opus-5-5"})
    s = settings.get_settings()
    assert (s.claude_cli_model, s.anthropic_model) == ("opus", "claude-opus-5-5")
    assert get_provider("claude_cli").model == "opus"
    # an empty model falls back to the default
    body = client.put("/api/settings/llm", json={"target": "claude_cli", "model": ""}).json()
    assert opt(body, "claude_cli")["model"] == "sonnet"


def test_rejects_bad_input(client):
    assert client.put("/api/settings/llm", json={"target": "nope"}).status_code == 404
    assert client.put("/api/settings/llm", json={"target": "claude_cli", "api_key": "x"}).status_code == 422
    assert client.post("/api/settings/llm/test/nope").status_code == 404
    with pytest.raises(ValueError):
        store.save_overrides({"claude_cli_path": "/tmp/evil"})


def test_test_endpoint_short_circuits_without_key(client):
    body = client.post("/api/settings/llm/test/anthropic_api").json()
    assert body == {"ok": False, "error": "No API key saved yet.", "latency_s": 0}


def test_legacy_llm_model_maps_to_the_env_provider(env, monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "nvidia")
    monkeypatch.setenv("LLM_MODEL", "nvidia/nemotron-x")
    settings.get_settings.cache_clear()
    s = settings.get_settings()
    assert s.nvidia_model == "nvidia/nemotron-x" and s.claude_cli_model == "" and s.openai_model == ""
    # an explicit per-provider variable wins over LLM_MODEL
    monkeypatch.setenv("NVIDIA_MODEL", "meta/x")
    settings.get_settings.cache_clear()
    assert settings.get_settings().nvidia_model == "meta/x"


def test_generic_openai_compat_still_works(env, monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "openai_compat")
    monkeypatch.setenv("LLM_MODEL", "qwen")
    settings.get_settings.cache_clear()
    p = get_provider()
    assert isinstance(p, OpenAICompatProvider) and p.base_url == "http://localhost:8080/v1" and p.model == "qwen"
    payload = p._payload([{"role": "user", "content": "hi"}], 0.0, 10, False, False)
    assert payload["max_tokens"] == 10 and "max_completion_tokens" not in payload


def test_openai_api_payload(env, monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", FAKE_KEY)
    monkeypatch.setenv("OPENAI_MODEL", "m")
    settings.get_settings.cache_clear()
    p = get_provider("openai_api")
    payload = p._payload([{"role": "user", "content": "hi"}], 0.0, 10, True, False)
    assert payload["max_completion_tokens"] == 10 and "temperature" not in payload
    assert payload["response_format"] == {"type": "json_object"}


def test_saved_file_ignores_unknown_keys(env):
    env.write_text('{"llm_provider": "nvidia", "claude_cli_path": "/tmp/evil", "nvidia_model": 3}')
    assert store.load_overrides() == {"llm_provider": "nvidia"}


def test_codex_command_and_stdin(tmp_path):
    cmd = build_command("/bin/codex", tmp_path / "a.txt", "")
    assert cmd[:2] == ["/bin/codex", "exec"] and "--model" not in cmd and cmd[-1] == "-"
    assert cmd[cmd.index("--sandbox") + 1] == "read-only" and "--ephemeral" in cmd
    assert "--model" in build_command("/bin/codex", tmp_path / "a.txt", "m1")
    text = build_stdin([{"role": "system", "content": "SYS"}, {"role": "user", "content": "PROMPT"}], True)
    assert text.index("SYS") < text.index("PROMPT") and "JSON" in text and "Do not run commands" in text


def test_codex_exit_handling():
    check_exit(0, '{"ok": true}', "")
    with pytest.raises(LLMError, match="codex login") as e:
        check_exit(1, "", "Error: not logged in")
    assert e.value.retryable is False
    with pytest.raises(LLMError, match="empty answer"):
        check_exit(0, "", "")


def test_legacy_openai_placeholder_is_not_a_key(env, monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "not-needed")
    settings.get_settings.cache_clear()
    assert settings.get_settings().openai_api_key == ""
