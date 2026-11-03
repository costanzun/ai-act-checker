#!/usr/bin/env bash
# One command to run the EU AI Act Checker locally.
#   ./start.sh            # backend on :8101 + frontend on :3101
#   ./start.sh --setup    # only prepare (venv, deps, corpus, index, models)
#   ./start.sh --backend  # backend only
#   ./start.sh --frontend # frontend only
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"

API_PORT="${API_PORT:-8101}"
FRONTEND_PORT="${FRONTEND_PORT:-3101}"
export HF_HOME="${HF_HOME:-$ROOT/data/models}"
export NEXT_TELEMETRY_DISABLED=1

log() { printf '\033[1;34m[start]\033[0m %s\n' "$*"; }
die() { printf '\033[1;31m[start] %s\033[0m\n' "$*" >&2; exit 1; }

command -v uv >/dev/null 2>&1 || die "uv is required (https://docs.astral.sh/uv/). Install: curl -LsSf https://astral.sh/uv/install.sh | sh"
command -v pnpm >/dev/null 2>&1 || die "pnpm is required (npm i -g pnpm, or corepack enable)"

[ -f .env ] || { log "No .env found; copying .env.example (default provider: claude_cli)"; cp .env.example .env; }
set -a; . ./.env; set +a

MODE="${1:---all}"

setup() {
  log "Python environment (uv, Python 3.12)"
  (cd backend && uv sync -q -p 3.12 --extra dev)
  PY="$ROOT/backend/.venv/bin/python"

  if [ ! -f data/corpus/en.json ] || [ ! -f data/corpus/it.json ]; then
    [ -f data/raw/ai-act-consolidated-20260727-EN.xhtml ] || "$PY" scripts/fetch_law.py
    log "Building corpus (EN, IT)"; "$PY" scripts/build_corpus.py
  fi
  if [ -d data/raw/guidance ] && [ -z "$(ls -A data/guidance 2>/dev/null)" ]; then
    log "Building guidance corpus"; "$PY" scripts/build_guidance.py || true
  fi
  log "Embedding models (BGE-M3, bge-reranker-v2-m3; ~4.6 GB on first run)"
  "$PY" scripts/download_models.py --embeddings-only
  if [ "${LLM_PROVIDER:-claude_cli}" = "local_mlx" ]; then
    log "Local LLM weights (${MLX_MODEL:-mlx-community/Qwen2.5-14B-Instruct-4bit})"
    "$PY" scripts/download_models.py --llm-only
  fi
  if [ ! -d data/index/provisions_en.lance ]; then
    log "Building retrieval index"; "$PY" scripts/build_index.py --lang all
  fi

  log "Frontend dependencies"
  (cd frontend && pnpm install --frozen-lockfile --silent 2>/dev/null || pnpm install --silent)
}

check_port() {
  if lsof -nP -iTCP:"$1" -sTCP:LISTEN >/dev/null 2>&1; then
    die "Port $1 is already in use. Stop that process or set API_PORT/FRONTEND_PORT."
  fi
}

PIDS=()
cleanup() { for p in "${PIDS[@]:-}"; do [ -n "$p" ] && kill "$p" 2>/dev/null || true; done; }
trap cleanup EXIT INT TERM

run_backend() {
  check_port "$API_PORT"
  log "Backend → http://localhost:$API_PORT (provider: ${LLM_PROVIDER:-claude_cli}, model: ${LLM_MODEL:-sonnet})"
  (cd backend && exec .venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port "$API_PORT") &
  PIDS+=("$!")
}

run_frontend() {
  check_port "$FRONTEND_PORT"
  log "Frontend → http://localhost:$FRONTEND_PORT"
  (cd frontend && NEXT_PUBLIC_API_URL="http://localhost:$API_PORT" exec pnpm dev -p "$FRONTEND_PORT") &
  PIDS+=("$!")
}

case "$MODE" in
  --setup) setup ;;
  --backend) setup; run_backend; wait ;;
  --frontend) (cd frontend && pnpm install --silent); run_frontend; wait ;;
  --all|*) setup; run_backend; run_frontend
    log "Open http://localhost:$FRONTEND_PORT  (Ctrl-C stops both)"; wait ;;
esac
