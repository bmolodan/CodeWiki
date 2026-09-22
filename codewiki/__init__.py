"""
CodeWiki: Transform codebases into comprehensive documentation using AI-powered analysis.

This package provides a CLI tool for generating documentation from code repositories,
and an MCP server for IDE-driven documentation generation.
"""

# Note: the tokenizer is built lazily and directly from the bundled encoding
# ranks (see codewiki/_tiktoken_setup.py and codewiki/src/be/utils.py) without
# touching os.environ, so tokenization works offline after `pip install .`. If
# the user sets TIKTOKEN_CACHE_DIR (incl. from .env), CodeWiki defers to
# tiktoken's own resolution so the explicit choice wins.

__version__ = "2.0.0"
__author__ = "CodeWiki Contributors"
__license__ = "MIT"

__all__ = ["__version__"]
