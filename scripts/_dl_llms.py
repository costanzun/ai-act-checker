"""One-off helper used by the coordinator to pre-download local LLM weights (HF_HOME must be set)."""
import os, time, sys
from huggingface_hub import snapshot_download
for repo in ["mlx-community/Qwen2.5-3B-Instruct-4bit", "mlx-community/Qwen2.5-14B-Instruct-4bit"]:
    t = time.time()
    p = snapshot_download(repo)
    print(f"{repo} -> {p} in {time.time()-t:.0f}s", flush=True)
print("DONE", flush=True)
