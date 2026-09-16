"""
CodeWiki: Transform codebases into comprehensive documentation using AI-powered analysis.

This package provides a CLI tool for generating documentation from code repositories,
and an MCP server for IDE-driven documentation generation.
"""

# Point tiktoken at the bundled encoding cache before any submodule that uses
# tiktoken is imported, so tokenization works offline after `pip install .`.
# Runs at package import (i.e. before codewiki.* submodules) and preserves an
# explicit user-provided TIKTOKEN_CACHE_DIR.
from codewiki._tiktoken_setup import configure_cache as _configure_tiktoken_cache

_configure_tiktoken_cache()

__version__ = "1.0.1"
__author__ = "CodeWiki Contributors"
__license__ = "MIT"

__all__ = ["__version__"]

