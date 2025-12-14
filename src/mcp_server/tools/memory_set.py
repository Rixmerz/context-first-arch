"""
MCP Tool: memory.set

Store project learnings in persistent memory.
"""

from typing import Any, Dict, List, Optional
from pathlib import Path

from src.core.memory_store import MemoryStore


async def memory_set(
    project_path: str,
    key: str,
    value: str,
    tags: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Store a memory in the project knowledge base.

    Memories are persisted in SQLite and can be retrieved across sessions.
    Useful for storing architectural decisions, lessons learned, patterns, etc.

    Args:
        project_path: Path to CFA project
        key: Unique identifier for the memory
        value: Content to store
        tags: Optional list of tags for categorization

    Returns:
        Dictionary with:
            - success: Boolean
            - key: Memory key
            - timestamp: When memory was stored
            - tags: Applied tags

    Example:
        result = await memory_set(
            project_path="/projects/my-app",
            key="auth-decision",
            value="Decided to use JWT for authentication due to stateless requirements",
            tags=["architecture", "security", "auth"]
        )
    """
    try:
        path = Path(project_path)

        # Validate CFA project
        if not (path / ".claude").exists():
            return {"success": False, "error": "Not a CFA project (missing .claude/)"}

        # Validate inputs
        if not key or not key.strip():
            return {"success": False, "error": "Memory key cannot be empty"}

        if not value or not value.strip():
            return {"success": False, "error": "Memory value cannot be empty"}

        # Store memory
        store = MemoryStore(path)
        memory = store.set(key=key.strip(), value=value.strip(), tags=tags or [])

        return {
            "success": True,
            "key": memory.key,
            "timestamp": memory.timestamp,
            "tags": memory.tags,
            "message": f"✓ Stored memory '{key}'" + (f" with tags: {', '.join(memory.tags)}" if memory.tags else "")
        }

    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to store memory: {str(e)}"
        }
