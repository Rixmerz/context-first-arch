"""
Features Module - CFA v3 Domain Functionality

Each feature follows CFA v2 architecture:
- core/: Business logic and storage
- tools/: MCP tool wrappers

## Available Features (7)

- **analysis**: Code analysis (dependencies, coupling, impact, patterns)
- **contract**: Interface documentation
- **knowledge_graph**: Intelligent context retrieval
- **memory**: Persistent key-value storage
- **orchestration**: Safe points for git checkpoints
- **rules**: Business logic capture
- **workflow**: Session onboarding
"""

# Re-export for convenience
from .memory import Memory, MemoryStore

__all__ = ["Memory", "MemoryStore"]
