"""Bundled tiktoken cache bootstrap.

tiktoken downloads its BPE encoding files from
``openaipublic.blob.core.windows.net`` on first use and caches them under
``TIKTOKEN_CACHE_DIR``. On an offline / air-gapped machine that download fails
with a long SSL traceback. To make CodeWiki work after ``pip install .`` with no
network, the required encoding files are vendored inside the installed package
at ``codewiki/resources/tiktoken_cache/`` and this module points
``TIKTOKEN_CACHE_DIR`` at them.

Resolution is relative to the installed package (``__file__``), never the current
working directory, so it behaves identically from a source checkout, a wheel in
site-packages, and CI.

tiktoken names each cache file ``sha1(<blob-url>).hexdigest()``. The mapping
below records, for every encoding CodeWiki requires, that cache-file name plus
the sha256 of the file contents so the vendored blob is reproducible/verifiable.
"""

from __future__ import annotations

import os
from pathlib import Path

# Directory bundled into the package (see pyproject package-data / MANIFEST.in).
BUNDLED_CACHE_DIR = Path(__file__).resolve().parent / "resources" / "tiktoken_cache"

# Encodings CodeWiki actually loads. Currently only cl100k_base
# (tiktoken.encoding_for_model("gpt-4"), used by count_tokens). Each entry maps
# the encoding name to the tiktoken cache-file name — sha1 of the blob URL
# "https://openaipublic.blob.core.windows.net/encodings/<name>.tiktoken" — and
# the sha256 of the file contents for verification.
REQUIRED_ENCODINGS: dict[str, dict[str, str]] = {
    "cl100k_base": {
        "cache_file": "9b5ad71b2ce5302211f9c61530b329a4922fc6a4",
        "sha256": "223921b76ee99bde995b7ff738513eef100fb51d18c93597a113bcffe865b2a7",
    },
}


def configure_cache() -> None:
    """Point ``TIKTOKEN_CACHE_DIR`` at the bundled cache unless already set.

    Uses ``setdefault`` so an explicit user-provided ``TIKTOKEN_CACHE_DIR`` is
    preserved. Must run before any module that calls ``tiktoken.get_encoding``
    is imported; CodeWiki calls it from ``codewiki/__init__.py``.
    """
    os.environ.setdefault("TIKTOKEN_CACHE_DIR", str(BUNDLED_CACHE_DIR))


def _active_cache_dir() -> str:
    return os.environ.get("TIKTOKEN_CACHE_DIR", str(BUNDLED_CACHE_DIR))


def ensure_encoding_available(name: str) -> None:
    """Fail fast with an actionable message if a required encoding is missing.

    Only enforced when CodeWiki is using its own bundled cache directory. If the
    user pointed ``TIKTOKEN_CACHE_DIR`` at a custom location we leave the outcome
    to tiktoken (they may intend an online download or a different layout).

    Raising here avoids the opaque SSL/connection traceback tiktoken would emit
    when it silently falls back to a network fetch on an offline machine.
    """
    spec = REQUIRED_ENCODINGS.get(name)
    if spec is None:
        return

    active = _active_cache_dir()
    if Path(active).resolve() != BUNDLED_CACHE_DIR.resolve():
        # User-provided cache dir — respect it, don't second-guess.
        return

    cache_file = BUNDLED_CACHE_DIR / spec["cache_file"]
    if not cache_file.exists():
        raise RuntimeError(
            f"Required tiktoken encoding '{name}' is not bundled "
            f"(expected {cache_file}).\n"
            "Run scripts/prepare_tiktoken_cache.py on an Internet-connected "
            "machine to populate codewiki/resources/tiktoken_cache/, or set "
            "TIKTOKEN_CACHE_DIR to a directory that already contains it."
        )
