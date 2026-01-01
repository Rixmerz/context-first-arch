"""
Knowledge Graph Tools - MCP Tool Wrappers

10 tools consolidated to 6 in MCP:
- Build/Status (2): kg_build, kg_status
- Retrieval (1): kg_retrieve (includes omission info)
- Context (3→1): kg_expand, kg_get, kg_related → kg.context
- Search (1): kg_search
- Git (3→1): kg_history, kg_blame, kg_diff → kg.git
"""

from .kg_build import kg_build
from .kg_status import kg_status
from .kg_retrieve import kg_retrieve
from .kg_expand import kg_expand
from .kg_get import kg_get
from .kg_search import kg_search
from .kg_related import kg_related
from .kg_history import kg_history
from .kg_blame import kg_blame
from .kg_diff import kg_diff

__all__ = [
    "kg_build", "kg_status", "kg_retrieve", "kg_expand", "kg_get", "kg_search",
    "kg_related", "kg_history", "kg_blame", "kg_diff",
]
