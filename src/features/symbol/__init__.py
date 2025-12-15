"""
Symbol Feature - Semantic Code Operations

LSP-powered symbol operations for AI agents:
- Symbol discovery and navigation
- Reference tracking
- Semantic code modifications
- Multi-language support (30+ languages)

## Usage

```python
from src.features.symbol import find_symbol, replace_symbol_body

# Find a symbol
result = find_symbol(project_path, "MyClass")

# Replace symbol body
replace_symbol_body(project_path, "file.py", "my_function", "new code...")
```
"""

from .core import (
    LSPManager, get_lsp_manager,
    find_symbol, find_references, get_symbols_overview,
    replace_symbol_body, insert_after_symbol, insert_before_symbol, rename_symbol,
)

__all__ = [
    "LSPManager", "get_lsp_manager",
    "find_symbol", "find_references", "get_symbols_overview",
    "replace_symbol_body", "insert_after_symbol", "insert_before_symbol", "rename_symbol",
]
