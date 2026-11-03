#!/usr/bin/env python3
"""Download the Hugging Face models used by the app into HF_HOME (default data/models).

  python scripts/download_models.py                  # everything (~10 GB)
  python scripts/download_models.py --embeddings-only
  python scripts/download_models.py --llm-only
  python scripts/download_models.py --small-only     # only the small MLX model
"""
from __future__ import annotations

import argparse
import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

EMBEDDINGS = ["BAAI/bge-m3", "BAAI/bge-reranker-v2-m3"]
# skip ONNX duplicates and images (not used by sentence-transformers / torch)
IGNORE = ["onnx/*", "imgs/*", "*.onnx", "*.onnx_data", "long.jpg"]
LLM = ["mlx-community/Qwen2.5-14B-Instruct-4bit"]
SMALL = ["mlx-community/Qwen2.5-3B-Instruct-4bit"]


def _load_env() -> None:
    """Fill os.environ from .env files without overriding real env vars."""
    for f in (ROOT / "backend" / ".env", ROOT / ".env"):  # first one found wins for a key
        if not f.exists():
            continue
        for line in f.read_text().splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


def _dir_size(p: Path) -> int:
    # snapshot files are symlinks into blobs/; stat() follows them
    return sum(f.stat().st_size for f in p.rglob("*") if f.is_file())


def _fmt(n: int) -> str:
    return f"{n / 1e9:.2f} GB" if n >= 1e9 else f"{n / 1e6:.1f} MB"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    g = ap.add_mutually_exclusive_group()
    g.add_argument("--embeddings-only", action="store_true")
    g.add_argument("--llm-only", action="store_true", help="the 14B and 3B MLX models")
    g.add_argument("--small-only", action="store_true", help="only the 3B MLX model")
    ap.add_argument("--extra", action="append", default=[], help="additional repo id (repeatable)")
    a = ap.parse_args()

    _load_env()
    hf_home = Path(os.environ.get("HF_HOME", "data/models")).expanduser()
    if not hf_home.is_absolute():
        hf_home = ROOT / hf_home
    hf_home.mkdir(parents=True, exist_ok=True)
    os.environ["HF_HOME"] = str(hf_home)
    os.environ.setdefault("HF_HUB_DISABLE_TELEMETRY", "1")

    from huggingface_hub import snapshot_download  # import after HF_HOME is set

    if a.embeddings_only:
        repos = list(EMBEDDINGS)
    elif a.small_only:
        repos = list(SMALL)
    elif a.llm_only:
        repos = LLM + SMALL
    else:
        repos = EMBEDDINGS + LLM + SMALL
    repos += a.extra

    print(f"HF_HOME = {hf_home}")
    total = 0
    t_all = time.time()
    for repo in repos:
        t0 = time.time()
        try:
            # Fast path: complete local snapshot present -> skip network entirely.
            try:
                path = snapshot_download(repo, local_files_only=True, ignore_patterns=IGNORE)
                status = "present, skipped"
            except Exception:
                path = snapshot_download(repo, ignore_patterns=IGNORE)
                status = f"downloaded in {time.time() - t0:.0f}s"
        except Exception as e:  # noqa: BLE001
            print(f"[FAIL] {repo}: {e}", file=sys.stderr)
            return 1
        size = _dir_size(Path(path))
        total += size
        print(f"[ok]   {repo}: {_fmt(size)} ({status})")
    print(f"total {_fmt(total)} in {time.time() - t_all:.0f}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
