"""
Memory Tools - MCP Tool Wrappers

Thin wrappers that delegate to the core MemoryStore.
Each tool follows CFA v2 pattern: 1 file = 1 MCP function.
"""

from .memory_set import memory_set
from .memory_get import memory_get
from .memory_search import memory_search
from .memory_list import memory_list
from .memory_delete import memory_delete

__all__ = [
    "memory_set",
    "memory_get",
    "memory_search",
    "memory_list",
    "memory_delete",
]
