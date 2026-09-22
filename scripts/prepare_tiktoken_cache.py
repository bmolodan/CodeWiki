#!/usr/bin/env python3
"""Populate the vendored tiktoken encoding cache.

Run this on an Internet-connected machine to download the tiktoken encodings
CodeWiki requires into ``codewiki/resources/tiktoken_cache/`` so they can be
bundled into the wheel/sdist and used offline after ``pip install .``.

Usage:
    python scripts/prepare_tiktoken_cache.py [--verify]

It sets ``TIKTOKEN_CACHE_DIR`` to the bundled directory, asks tiktoken to load
each required encoding (which downloads and caches it there), then verifies the
resulting cache file against the recorded sha256.

Requires the ``tiktoken`` package to be installed.
"""

from __future__ import annotations

import argparse
import hashlib
import os
import sys
from pathlib import Path

# Make `codewiki` importable when run from a source checkout without install.
REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from codewiki._tiktoken_setup import BUNDLED_CACHE_DIR, REQUIRED_ENCODINGS  # noqa: E402


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--verify",
        action="store_true",
        help="Only verify existing cache files; do not download.",
    )
    args = parser.parse_args()

    BUNDLED_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    # Direct tiktoken's downloads/reads at the bundled directory.
    os.environ["TIKTOKEN_CACHE_DIR"] = str(BUNDLED_CACHE_DIR)

    if not args.verify:
        try:
            import tiktoken
        except ImportError:
            print(
                "ERROR: the 'tiktoken' package is required to download encodings.\n"
                "Install it (pip install tiktoken) and re-run.",
                file=sys.stderr,
            )
            return 2

        for name in REQUIRED_ENCODINGS:
            print(f"Loading encoding '{name}' (downloads if missing) ...")
            tiktoken.get_encoding(name)

    # Verify every required encoding is present with the expected checksum.
    ok = True
    for name, spec in REQUIRED_ENCODINGS.items():
        cache_file = BUNDLED_CACHE_DIR / spec["cache_file"]
        if not cache_file.exists():
            print(f"MISSING: {name} -> {cache_file}", file=sys.stderr)
            ok = False
            continue
        digest = _sha256(cache_file)
        expected = spec["sha256"]
        if digest != expected:
            print(
                f"CHECKSUM MISMATCH for {name}: got {digest}, expected {expected}",
                file=sys.stderr,
            )
            ok = False
        else:
            print(f"OK: {name} -> {cache_file.name} (sha256 {digest})")

    if not ok:
        return 1
    print(f"\nAll required encodings present in {BUNDLED_CACHE_DIR}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
