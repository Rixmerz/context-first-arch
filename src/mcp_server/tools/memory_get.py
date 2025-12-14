"""
MCP Tool: memory.get

Retrieve project learnings from persistent memory.
"""

from typing import Any, Dict
from pathlib import Path

from src.core.memory_store import MemoryStore


async def memory_get(
    project_path: str,
    key: str
) -> Dict[str, Any]:
    """
    Retrieve a memory from the project knowledge base.

    Args:
        project_path: Path to CFA project
        key: Memory identifier

    Returns:
        Dictionary with:
            - success: Boolean
            - key: Memory key
            - value: Stored content
            - timestamp: When memory was stored
            - tags: Associated tags

    Example:
        result = await memory_get(
            project_path="/projects/my-app",
            key="auth-decision"
        )
    """
    try:
        path = Path(project_path)

        # Validate CFA project
        if not (path / ".claude").exists():
            return {"success": False, "error": "Not a CFA project (missing .claude/)"}

        # Retrieve memory
        store = MemoryStore(path)
        memory = store.get(key)

        if not memory:
            return {
                "success": False,
                "error": f"Memory not found: {key}",
                "hint": "Use memory.search to find available memories"
            }

        return {
            "success": True,
            "key": memory.key,
            "value": memory.value,
            "timestamp": memory.timestamp,
            "tags": memory.tags,
            "message": f"✓ Retrieved memory '{key}'"
        }

    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to retrieve memory: {str(e)}"
        }
