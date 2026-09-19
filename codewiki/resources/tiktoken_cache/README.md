# Vendored tiktoken encoding cache

This directory holds the [tiktoken](https://github.com/openai/tiktoken) BPE
encoding files that CodeWiki needs, bundled into the installed package.

## Why these files are vendored

tiktoken downloads its encoding files from
`https://openaipublic.blob.core.windows.net/encodings/` on first use and caches
them under `TIKTOKEN_CACHE_DIR`. On an offline / air-gapped machine that download
fails with a long SSL traceback, and CodeWiki cannot tokenize text.

Bundling the files inside the package and pointing `TIKTOKEN_CACHE_DIR` at this
directory (done automatically in `codewiki/__init__.py` via
`codewiki/_tiktoken_setup.py`) makes tokenization work with no network after
`pip install .`. The path is resolved relative to the installed package, so it
behaves the same from a source checkout, a wheel in `site-packages`, and CI.

## File naming

tiktoken names each cache file `sha1(<blob-url>).hexdigest()`, so the filenames
here are opaque hashes rather than `*.tiktoken`. That is expected — tiktoken
looks them up by that hash.

## Bundled encodings

| Encoding | Used by | Cache file (sha1 of URL) | Contents sha256 |
|----------|---------|--------------------------|-----------------|
| `cl100k_base` | `tiktoken.encoding_for_model("gpt-4")` in `codewiki/src/be/utils.py` (`count_tokens`) | `9b5ad71b2ce5302211f9c61530b329a4922fc6a4` | `223921b76ee99bde995b7ff738513eef100fb51d18c93597a113bcffe865b2a7` |

**Upstream source:**
`https://openaipublic.blob.core.windows.net/encodings/cl100k_base.tiktoken`

The authoritative list (encoding name → cache-file name → sha256) lives in
`REQUIRED_ENCODINGS` in `codewiki/_tiktoken_setup.py`.

## Regenerating / updating

On an Internet-connected machine:

```bash
python scripts/prepare_tiktoken_cache.py           # download + verify
python scripts/prepare_tiktoken_cache.py --verify  # verify only
```

The script downloads each required encoding into this directory and checks it
against the recorded sha256. If CodeWiki starts requiring another encoding, add
it to `REQUIRED_ENCODINGS` and re-run the script.

## Overriding the bundled cache

Set `TIKTOKEN_CACHE_DIR` yourself (in the shell or in the project's `.env`) to
use a different cache location. CodeWiki only points tiktoken at the bundled
directory **while loading its own encoder**, and only when you haven't set the
variable — so an explicit value always wins, and the process is never left
pinned to the (possibly read-only) `site-packages` cache for other tiktoken use.
