"""
Memory Feature - Persistent Project Memory

This feature provides persistent key-value storage for project learnings,
decisions, and context. Uses SQLite for durability.

## Architecture (CFA v2 Pattern)

```
features/memory/
├── core/
│   └── memory_store.py    # Business logic + SQLite storage
├── tools/
│   ├── memory_set.py      # MCP tool wrapper
│   ├── memory_get.py      # MCP tool wrapper
│   ├── memory_search.py   # MCP tool wrapper
│   ├── memory_list.py     # MCP tool wrapper
│   └── memory_delete.py   # MCP tool wrapper
└── tests/
    └── test_memory_store.py
```

## Usage

```python
from src.features.memory import MemoryStore, Memory

# Initialize store for a project
store = MemoryStore(project_path)

# Store a memory
memory = store.set("api-patterns", "Use REST for public, gRPC for internal", tags=["architecture"])

# Retrieve
memory = store.get("api-patterns")

# Search
results = store.search(query="REST", tags=["architecture"])
```
"""

from .core import Memory, MemoryStore

__all__ = ["Memory", "MemoryStore"]
