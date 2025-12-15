"""
Features Module - Domain-Specific Functionality

Each feature is a self-contained module following CFA v2 architecture:
- core/: Business logic and storage
- tools/: MCP tool wrappers (thin delegation)
- tests/: Feature-specific tests

## Available Features

- **memory**: Persistent key-value storage with tagging
"""

# Re-export for convenience
from .memory import Memory, MemoryStore

__all__ = ["Memory", "MemoryStore"]
