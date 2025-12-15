"""
Symbol Core Module - LSP Integration

IDE-like semantic code analysis for AI agents.
Multi-language support via multilspy (30+ languages).
"""

from .manager import LSPManager, get_lsp_manager
from .symbols import (
    find_symbol,
    find_references,
    get_symbols_overview,
    replace_symbol_body,
    insert_after_symbol,
    insert_before_symbol,
    rename_symbol,
)

__all__ = [
    "LSPManager", "get_lsp_manager",
    "find_symbol", "find_references", "get_symbols_overview",
    "replace_symbol_body", "insert_after_symbol", "insert_before_symbol", "rename_symbol",
]
