#!/usr/bin/env python
"""Download (or just check) the legal source files from the EU Publications Office Cellar.

Content negotiation against ``http://publications.europa.eu/resource/celex/<CELEX>``
with ``Accept: application/xhtml+xml`` and ``Accept-Language: eng|ita`` (the EUR-Lex
HTML endpoint answers scripts with an empty 202; Cellar does not).

Files written to ``data/raw`` (skipped if present unless ``--force``):

* ``ai-act-consolidated-<YYYYMMDD>-{EN,IT}.xhtml``: consolidated text (``02024R1689-<date>``)
* ``ai-act-original-2024-1689-{EN,IT}.xhtml``: Official Journal text (``32024R1689``), used for
  the recitals, which consolidations omit

``--check-only`` downloads nothing; it reads the Cellar notice (branch, falling back to tree/object) of ``32024R1689`` and prints every
consolidated version (``02024R1689-YYYYMMDD``) found, flagging one newer than the pinned date.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parents[1]
BASE = "http://publications.europa.eu/resource/celex/"
CONSOLIDATED_DATE = "20260727"
BASE_CELEX = "32024R1689"
UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
)
LANGS = {"EN": "eng", "IT": "ita"}


def _client() -> httpx.Client:
    return httpx.Client(follow_redirects=True, timeout=180, headers={"User-Agent": UA})


NOTICE_KINDS = ("branch", "tree", "object")  # "branch" currently answers 400; tree/object work


def check_versions(client: httpx.Client) -> list[str]:
    """Return consolidated versions (``YYYYMMDD``) listed in the Cellar notice of the base act."""
    last: httpx.HTTPError | None = None
    for kind in NOTICE_KINDS:
        try:
            r = client.get(BASE + BASE_CELEX, headers={"Accept": f"application/xml;notice={kind}"})
            r.raise_for_status()
        except httpx.HTTPError as e:
            last = e
            continue
        return sorted(set(re.findall(r"02024R1689-(\d{8})", r.text)))
    raise last or RuntimeError("no notice kind worked")


def report_versions(client: httpx.Client) -> None:
    """Print consolidated versions and whether a newer one than the pinned date exists."""
    try:
        versions = check_versions(client)
    except httpx.HTTPError as e:
        print(f"could not read the Cellar notice: {e}", file=sys.stderr)
        return
    if not versions:
        print("no consolidated versions found in the notice")
        return
    print("consolidated versions found: " + ", ".join(versions))
    newer = [v for v in versions if v > CONSOLIDATED_DATE]
    if newer:
        print(f"NEWER consolidation available: {newer[-1]} (pinned: {CONSOLIDATED_DATE})")
    else:
        print(f"pinned consolidation {CONSOLIDATED_DATE} is the latest")


def download(client: httpx.Client, celex: str, lang: str, dest: Path, force: bool) -> None:
    """Download one file unless it exists (and not ``force``)."""
    if dest.exists() and not force:
        print(f"skip (exists): {dest.name}")
        return
    r = client.get(BASE + celex, headers={"Accept": "application/xhtml+xml", "Accept-Language": LANGS[lang]})
    r.raise_for_status()
    if b"<html" not in r.content[:2000].lower() and b"<?xml" not in r.content[:100]:
        raise RuntimeError(f"{celex} [{lang}]: unexpected payload ({r.headers.get('content-type')})")
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(r.content)
    print(f"wrote {dest} ({len(r.content):,} bytes)")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--check-only", action="store_true", help="only report available consolidated versions")
    ap.add_argument("--force", action="store_true", help="re-download files that already exist")
    ap.add_argument("--raw-dir", type=Path, default=ROOT / "data" / "raw")
    args = ap.parse_args()

    with _client() as client:
        report_versions(client)
        if args.check_only:
            return 0
        for lang in LANGS:
            download(
                client, f"02024R1689-{CONSOLIDATED_DATE}", lang,
                args.raw_dir / f"ai-act-consolidated-{CONSOLIDATED_DATE}-{lang}.xhtml", args.force,
            )
            download(
                client, BASE_CELEX, lang, args.raw_dir / f"ai-act-original-2024-1689-{lang}.xhtml", args.force
            )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
