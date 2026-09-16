"""
CodeWiki: Transform codebases into comprehensive documentation using AI-powered analysis.

This package provides a CLI tool for generating documentation from code repositories,
and an MCP server for IDE-driven documentation generation.
"""

# Note: tiktoken is pointed at the bundled encoding cache lazily, scoped to the
# encoder load (see codewiki/_tiktoken_setup.py and codewiki/src/be/utils.py),
# rather than process-wide here — so a user TIKTOKEN_CACHE_DIR (incl. one from
# .env, loaded later) still wins and the process isn't pinned to a read-only
# site-packages cache.

__version__ = "1.0.1"
__author__ = "CodeWiki Contributors"
__license__ = "MIT"

__all__ = ["__version__"]

