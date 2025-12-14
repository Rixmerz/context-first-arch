"""
LSP (Language Server Protocol) integration for semantic code analysis.

Provides IDE-like capabilities for AI agents:
- Symbol discovery and navigation
- Reference tracking
- Semantic code modifications
- Multi-language support (30+ languages via multilspy)
"""

from src.core.lsp.manager import LSPManager, get_lsp_manager
from src.core.lsp.symbols import (
    find_symbol,
    find_references,
    get_symbols_overview,
    replace_symbol_body,
    insert_after_symbol,
    insert_before_symbol,
    rename_symbol,
)

__all__ = [
    # Manager
    "LSPManager",
    "get_lsp_manager",
    # Symbol operations
    "find_symbol",
    "find_references",
    "get_symbols_overview",
    "replace_symbol_body",
    "insert_after_symbol",
    "insert_before_symbol",
    "rename_symbol",
]
