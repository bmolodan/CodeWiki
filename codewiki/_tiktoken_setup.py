"""Bundled tiktoken encoding, loaded without touching the environment.

tiktoken downloads its BPE encoding files from
``openaipublic.blob.core.windows.net`` on first use and caches them under
``TIKTOKEN_CACHE_DIR``. On an offline / air-gapped machine that download fails
with a long SSL traceback. To make CodeWiki work after ``pip install .`` with no
network, the required encoding files are vendored inside the installed package at
``codewiki/resources/tiktoken_cache/`` and this module builds the encoder
directly from them.

The default path constructs a ``tiktoken.Encoding`` from the vendored ranks file
plus the vendored (pinned) encoding spec and **never touches ``os.environ``** —
so it is thread-safe, leaves no process-global state, and cannot be defeated by a
read-only ``site-packages`` cache. If the user has set ``TIKTOKEN_CACHE_DIR``
(the key is present — even an empty string, which tiktoken treats as "no cache"),
CodeWiki defers entirely to tiktoken's own resolution so the explicit choice
wins.

Paths are resolved relative to the installed package (``__file__``), never the
current working directory, so behaviour is identical from a source checkout, a
wheel in ``site-packages`` and CI.

tiktoken names each cache file ``sha1(<blob-url>).hexdigest()``. ``REQUIRED_ENCODINGS``
records that cache-file name plus the sha256 of the file contents so the vendored
blob is reproducible/verifiable. ``ENCODING_SPECS`` records the rest of the
(pinned, stable) encoding definition — the regex and special tokens — taken
verbatim from tiktoken's ``cl100k_base`` constructor. The offline tests assert
this reproduces ``tiktoken.get_encoding("cl100k_base")`` exactly.
"""

from __future__ import annotations

import base64
import hashlib
import os
from dataclasses import dataclass, field
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


@dataclass(frozen=True)
class EncodingSpec:
    """The non-ranks half of a tiktoken encoding definition (pinned, vendored)."""

    pat_str: str
    special_tokens: dict[str, int] = field(default_factory=dict)


# Verbatim from tiktoken's `cl100k_base` constructor (tiktoken_ext.openai_public).
# Pinned alongside the ranks file so the encoder can be built offline without any
# tiktoken registry/network access; the parity test guards these against the
# installed tiktoken.
ENCODING_SPECS: dict[str, EncodingSpec] = {
    "cl100k_base": EncodingSpec(
        pat_str=r"""'(?i:[sdmt]|ll|ve|re)|[^\r\n\p{L}\p{N}]?+\p{L}++|\p{N}{1,3}+| ?[^\s\p{L}\p{N}]++[\r\n]*+|\s++$|\s*[\r\n]|\s+(?!\S)|\s""",
        special_tokens={
            "<|endoftext|>": 100257,
            "<|fim_prefix|>": 100258,
            "<|fim_middle|>": 100259,
            "<|fim_suffix|>": 100260,
            "<|endofprompt|>": 100276,
        },
    ),
}


def ensure_encoding_available(name: str) -> None:
    """Fail fast with an actionable message if a required encoding is not bundled.

    Raising here avoids the opaque SSL/connection traceback tiktoken would emit
    when it silently falls back to a network fetch on an offline machine.
    """
    spec = REQUIRED_ENCODINGS.get(name)
    if spec is None:
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


def _load_bundled_ranks(name: str) -> dict[bytes, int]:
    """Read and parse the vendored BPE ranks for *name*.

    Verifies the file's sha256 against ``REQUIRED_ENCODINGS`` and parses the
    tiktoken bpe format (``<base64-token> <rank>`` per line) into the
    ``mergeable_ranks`` mapping — the same parse tiktoken's ``load_tiktoken_bpe``
    performs, but done here so no cache dir / environment / network is involved.
    """
    spec = REQUIRED_ENCODINGS[name]
    cache_file = BUNDLED_CACHE_DIR / spec["cache_file"]
    contents = cache_file.read_bytes()

    digest = hashlib.sha256(contents).hexdigest()
    if digest != spec["sha256"]:
        raise RuntimeError(
            f"Bundled tiktoken cache for '{name}' is corrupt: sha256 {digest} "
            f"!= expected {spec['sha256']} ({cache_file})."
        )

    ranks: dict[bytes, int] = {}
    for line in contents.splitlines():
        if not line:
            continue
        token, rank = line.split()
        ranks[base64.b64decode(token)] = int(rank)
    return ranks


def load_encoding_for_model(model_name: str, encoding_name: str):
    """Return a tiktoken encoding for *model_name*, offline via the bundled data.

    If ``TIKTOKEN_CACHE_DIR`` is set (present, even if empty), the user has opted
    into their own tiktoken cache/config, so we defer entirely to
    ``tiktoken.encoding_for_model`` and touch no bundled data. Otherwise we build
    the encoding directly from the vendored ranks + spec, without reading or
    writing ``os.environ`` (thread-safe; no site-packages writes).
    """
    import tiktoken

    if "TIKTOKEN_CACHE_DIR" in os.environ:
        # Explicit user cache/override wins — respect it, don't second-guess.
        return tiktoken.encoding_for_model(model_name)

    ensure_encoding_available(encoding_name)
    spec = ENCODING_SPECS[encoding_name]
    return tiktoken.Encoding(
        name=encoding_name,
        pat_str=spec.pat_str,
        mergeable_ranks=_load_bundled_ranks(encoding_name),
        special_tokens=dict(spec.special_tokens),
    )
