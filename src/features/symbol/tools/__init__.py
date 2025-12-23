"""
Symbol Tools - DEPRECATED

All symbol tools have been removed due to LSP indexing issues.
Use native Claude Code tools instead:
- symbol_find → file_search (MCP) or Grep (native)
- symbol_replace → Edit (native)
- symbol_references → file_search (MCP) or Grep (native)
- symbol_overview → file_read (MCP) or Read (native)
- symbol_insert → Edit (native)
- symbol_rename → Edit + file_search
- lsp_status/lsp_restart → N/A (no longer needed)
"""

__all__ = []
