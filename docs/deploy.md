# Deployment plan (not executed)

Nothing below has been run. It describes how the app would be hosted, in order of effort. Prerequisite for everything: the default `claude_cli` provider needs the Claude Code CLI logged in on the machine, which is not realistic on a server. **Production must use `LLM_PROVIDER=nvidia` or `anthropic_api`** (or `openai_compat` against your own server). Embeddings and reranking always run in the backend process, on CPU on most hosts.

## (a) Frontend on Vercel

```bash
cd frontend
vercel link                    # create or link the project
```

Project settings:

- Root directory: `frontend/`
- Framework preset: Next.js; install command `pnpm install`; build command `pnpm build` (`next build`)
- Environment variable (Production and Preview): `NEXT_PUBLIC_API_URL=https://<backend-host>`. It is inlined at build time, so redeploy after changing it.
- Do not set `NEXT_PUBLIC_MOCK_API` in production.

```bash
vercel env add NEXT_PUBLIC_API_URL production
vercel deploy --prod
```

The assessment endpoint streams over SSE straight from the browser to the backend, so the backend needs HTTPS and a CORS entry for the Vercel domain (below). TODO(coordinator): confirm the frontend calls the backend directly and not through a Next.js route handler.

## (b) Backend options

The backend needs about 5 GB for the embedding models, the corpus (`data/corpus`), the guidance (`data/guidance`) and the LanceDB index (`data/index`). Memory: plan for 4 GB or more (TODO(coordinator): measure resident memory with BGE-M3 and the reranker loaded). `local_mlx` is not available on Linux hosts.

Environment for production:

```
LLM_PROVIDER=nvidia                 # or anthropic_api
LLM_MODEL=nvidia/llama-3.3-nemotron-super-49b-v1
NVIDIA_API_KEY=...                  # or ANTHROPIC_API_KEY
LLM_MAX_CONCURRENCY=4
HF_HOME=/app/data/models
INDEX_DIR=/app/data/index
CORS_ORIGINS=https://<your-app>.vercel.app
```

`CORS_ORIGINS` is a comma-separated list (preview URLs need adding or a stable alias). Health check: `GET /health`.

### Dockerfile (snippet)

Written for the repository root as build context. The raw EUR-Lex files and the built corpus are copied in; the index is built at image build time so the container starts ready.

```dockerfile
FROM python:3.12-slim
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv
WORKDIR /app
ENV HF_HOME=/app/data/models UV_LINK_MODE=copy PYTHONUNBUFFERED=1

# dependencies first, for layer caching
COPY backend/pyproject.toml backend/uv.lock backend/
RUN cd backend && uv sync --frozen --no-dev -p 3.12 --no-install-project

COPY backend/ backend/
COPY scripts/ scripts/
COPY data/raw data/raw
COPY data/corpus data/corpus
COPY data/guidance data/guidance

# models: baked into the image (about 4.6 GB) ...
RUN backend/.venv/bin/python scripts/download_models.py --embeddings-only
# ... then the retrieval index
RUN backend/.venv/bin/python scripts/build_index.py --lang all

EXPOSE 8101
WORKDIR /app/backend
CMD [".venv/bin/python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8101"]
```

Alternative to baking in the models: skip the download step, mount a persistent volume at `/app/data/models` (and `/app/data/index`), and run the two scripts once. This keeps the image small and speeds up deploys, at the cost of a slow first start.

Notes: `uv sync --no-dev` pulls `torch` (large; consider the CPU wheel index to save about 2 GB) and skips `mlx-lm` automatically on Linux (it is darwin-only in `pyproject.toml`). `app/main.py` resolves the project root two levels above `app/` (here `/app`), so `data/corpus` must sit at `/app/data/corpus`, as in the snippet. TODO(coordinator): verify the build once with `docker build`.

### Fly.io

```bash
fly launch --no-deploy --name ai-act-checker-api --dockerfile Dockerfile   # internal_port 8101
fly volumes create models --size 10       # only if models are not baked in
fly secrets set LLM_PROVIDER=nvidia NVIDIA_API_KEY=... LLM_MODEL=... CORS_ORIGINS=https://<app>.vercel.app
fly scale vm shared-cpu-2x --memory 4096
fly deploy
```

In `fly.toml`: `[http_service] internal_port = 8101`, and a check `[[http_service.checks]] path = "/health" interval = "30s"`. Set `min_machines_running = 1` so the first request does not wait for the models to load.

### Railway

Create a service from the repository, set the Dockerfile path, add the variables above, expose port 8101, set the health check path to `/health`, and attach a volume at `/app/data/models` if the models are not baked in.

### Hetzner VM with Docker

```bash
# on the VM (e.g. CX32, 4 vCPU / 8 GB), with Docker installed
docker build -t ai-act-checker-api .
docker run -d --restart unless-stopped --name api -p 8101:8101 --env-file .env.prod ai-act-checker-api
```

Put Caddy or nginx in front for HTTPS (for example `api.example.org { reverse_proxy localhost:8101 }`). For SSE, disable response buffering (`flush_interval -1` in Caddy, `proxy_buffering off` in nginx).

## (c) Optional: Supabase / pgvector instead of LanceDB

Not implemented; LanceDB on local disk is enough for 1,600 provisions plus guidance and keeps the app fully local. It becomes worthwhile only if the index must be shared by several backend replicas, or edited without a rebuild.

```sql
create extension if not exists vector;

create table provisions (
  id        text not null,
  lang      text not null check (lang in ('en','it')),
  text      text not null,
  binding   boolean not null default true,
  embedding vector(1024) not null,       -- BGE-M3 dimension
  primary key (id, lang)
);
create index on provisions using hnsw (embedding vector_cosine_ops);
create index on provisions using gin (to_tsvector('simple', text));
```

Swap point: `backend/app/retrieval/index.py`. The `LanceIndex` class exposes `has`, `count`, `build`, `search_vector` and `search_fts`; a `PgVectorIndex` with the same methods (vector search with `embedding <=> $1`, full-text with `ts_rank`) would replace it, and `search.py` would keep fusing the two result lists (reciprocal rank fusion) and reranking. `scripts/build_index.py` would insert rows instead of writing Lance tables. The chunk metadata (`type`, binding flag, label) needs matching columns. TODO(coordinator): confirm the exact `LanceIndex` signature before writing the adapter.

## (d) Cost notes

- Vercel Hobby covers the static-ish frontend. Check the current terms before using it for anything commercial.
- Backend: a 4 GB shared VM on Fly.io or Railway, or a Hetzner CX32, is roughly in the range of 10 to 30 EUR per month; check current price lists. TODO(coordinator): fill in the actual figures at deploy time.
- LLM: `nvidia` free catalogue is rate-limited and not for production load. `anthropic_api` bills per token; the eval report gives tokens in and out per assessment, which gives a per-assessment cost for the chosen model.
- Embeddings run on the backend CPU; query latency is higher than on Apple Silicon (about 370 ms per query with reranking on the development machine). A 2-vCPU host will be slower; cache the LLM responses (`LLM_CACHE=1`) on a persistent volume.
- No database, authentication or storage costs unless the optional pgvector path is taken.
