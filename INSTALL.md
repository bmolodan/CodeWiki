# Installing CodeWiki from Source

This guide walks through installing CodeWiki from a source checkout, including
setting up the required Python version with a version manager.

## Prerequisites

- **Python 3.12+** — required (`pyproject.toml` sets `requires-python = ">=3.12"`;
  `pip install` refuses on older interpreters). See
  [Step 1](#1-install-python-312-with-a-version-manager) if you don't have it.
- **Git**
- **Node.js** — *optional*, only for Mermaid diagram validation. Skip it and set
  `MERMAID_VALIDATE=0` to disable validation (PythonMonkey-based validation is
  auto-disabled on Python 3.12+ regardless).

---

## 1. Install Python 3.12+ with a version manager

Using a version manager keeps CodeWiki's Python isolated from your system Python.
Pick the one for your platform.

### Option A — pyenv (macOS / Linux)

```bash
# Install pyenv (macOS)
brew install pyenv

# Install pyenv (Linux)
curl -fsSL https://pyenv.run | bash

# Add pyenv to your shell (zsh shown; use ~/.bashrc for bash), then restart the shell
cat >> ~/.zshrc <<'EOF'
export PYENV_ROOT="$HOME/.pyenv"
export PATH="$PYENV_ROOT/bin:$PATH"
eval "$(pyenv init -)"
EOF
exec "$SHELL"

# Install and select a 3.12 interpreter
pyenv install 3.12.7
pyenv shell 3.12.7          # this shell only (or: pyenv local 3.12.7 inside the repo)

# Verify
python --version            # -> Python 3.12.7
```

### Option B — uv (macOS / Linux / Windows)

[uv](https://docs.astral.sh/uv/) can fetch a standalone Python build for you:

```bash
# Install uv (macOS/Linux)
curl -LsSf https://astral.sh/uv/install.sh | sh
# Install uv (Windows PowerShell)
# powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

uv python install 3.12
```

### Option C — pyenv-win (Windows)

```powershell
# Install pyenv-win (PowerShell)
Invoke-WebRequest -UseBasicParsing -Uri https://raw.githubusercontent.com/pyenv-win/pyenv-win/master/pyenv-win/install-pyenv-win.ps1 -OutFile ./install-pyenv-win.ps1
&"./install-pyenv-win.ps1"
# Restart the terminal, then:
pyenv install 3.12.7
pyenv shell 3.12.7
python --version
```

---

## 2. Clone the repository

```bash
git clone https://github.com/FSoft-AI4Code/CodeWiki.git
cd CodeWiki
```

> Installing from a fork? Clone that instead and optionally check out a branch:
> ```bash
> git clone https://github.com/<your-user>/CodeWiki.git
> cd CodeWiki
> git checkout <branch>
> ```

## 3. Create and activate a virtual environment

Create the venv with your 3.12 interpreter (from Step 1).

**pyenv / system 3.12:**
```bash
python3.12 -m venv .venv          # or: python -m venv .venv  (if pyenv shell is 3.12)
source .venv/bin/activate         # Windows: .venv\Scripts\activate
```

**uv:**
```bash
uv venv --python 3.12
source .venv/bin/activate         # Windows: .venv\Scripts\activate
```

## 4. Install CodeWiki

```bash
# Editable install — source edits take effect without reinstalling
pip install -e .
```

This pulls every runtime dependency from `pyproject.toml` (tree-sitter parsers,
pydantic-ai, openai, litellm, fastapi, …) and installs the `codewiki` CLI.

For development (tests, linters — adds pytest/black/ruff):
```bash
pip install -e ".[dev]"
```

> Prefer uv for installs? `uv pip install -e .` works the same way.

## 5. Verify

```bash
codewiki --version
```

---

## 6. Configure an LLM provider

Settings are persisted to `~/.codewiki/config.json` and the API key is stored in
your OS keychain, both via `codewiki config set`. Every flag is optional and only
updates the keys you pass, so you can set things incrementally.

### Configure the endpoint

The endpoint is defined by `--provider` + `--base-url` (+ `--api-key`). Pick the
provider that matches your server:

```bash
# Local OpenAI-compatible server (vLLM / llama.cpp / LM Studio / Ollama, e.g. Qwen)
codewiki config set \
  --provider openai-compatible \
  --base-url http://localhost:8000/v1 \
  --api-key not-needed \
  --main-model qwen3.6-35b-a3b \
  --cluster-model qwen3.6-35b-a3b \
  --fallback-model qwen3.6-35b-a3b
```

- `--base-url` — the OpenAI-compatible endpoint. For local servers this is
  usually `http://<host>:<port>/v1`. Update just this flag if your server moves:
  `codewiki config set --base-url http://localhost:1234/v1`.
- `--api-key` — stored in the keychain. Local servers that don't check it still
  need a non-empty value (`not-needed` works).
- `--main-model` / `--cluster-model` / `--fallback-model` — model IDs as your
  endpoint advertises them (see your server's `/v1/models`).

Other providers set the endpoint differently (`--provider anthropic|bedrock|
azure-openai|atlas-cloud`, or `claude-code` / `codex` subscription mode which need
no base URL or key). See the [README](README.md) for full per-provider examples.

### New tuning parameters

These were added for running against local / hybrid-thinking models and can be
set persistently here, or overridden per run on `generate` (next step).

```bash
# Tool-call retries per agent before giving up (default: 3).
# Raise it for weaker/local models that emit malformed tool arguments.
codewiki config set --max-retries 5

# Reasoning/thinking mode. Off by default (hybrid-thinking models such as Qwen3
# emit <think> blocks that corrupt tool calls). Injected as
# chat_template_kwargs.enable_thinking=false; skipped for first-party APIs
# (OpenAI/Azure/Bedrock/Anthropic) that reject unknown fields.
codewiki config set --disable-thinking      # default
codewiki config set --enable-thinking       # opt back in (leave thinking on)
```

| Setting | Flag(s) | Default | Purpose |
|---------|---------|---------|---------|
| Max retries | `--max-retries N` (N ≥ 1) | `3` | Tool-call self-correction attempts per agent |
| Thinking mode | `--disable-thinking` / `--enable-thinking` | disabled | Turn hybrid-model reasoning off/on |

> Non-CLI (web app / MCP) callers can also set thinking via the `DISABLE_THINKING`
> environment variable (`true`/`false`, default `true`).

### Review and validate

```bash
codewiki config show          # print current config (API key masked)
codewiki config validate      # checks config + tests endpoint connectivity
```

## 7. Generate documentation

```bash
cd /path/to/your/repo
codewiki generate --verbose   # output written to ./docs
```

The tuning parameters above can be overridden for a single run (these take
precedence over the persisted config, which is otherwise used):

```bash
codewiki generate --max-retries 5 --enable-thinking --verbose
```

---

## Troubleshooting

- **`pip install` fails with a Python version error** — your active interpreter is
  older than 3.12. Re-check Step 1 (`python --version` inside the activated venv).
- **Mermaid validation warnings / Node.js errors** — `export MERMAID_VALIDATE=0`
  to disable diagram validation.
- **Clean reinstall** — `pip uninstall codewiki`, or simply delete `.venv` and
  redo Steps 3–4.

For architecture and contribution details, see [DEVELOPMENT.md](DEVELOPMENT.md).
