"""
MCP Tool: memory.delete

Delete a stored memory.
"""

from typing import Any, Dict
from pathlib import Path

from src.core.memory_store import MemoryStore


async def memory_delete(
    project_path: str,
    key: str
) -> Dict[str, Any]:
    """
    Delete a memory from the store.

    Permanently removes a memory by its key.

    Args:
        project_path: Path to the project root
        key: Memory identifier to delete

    Returns:
        Dictionary with:
            - success: Boolean
            - key: Deleted memory key
            - deleted: Whether deletion occurred
            - message: Status message

    Example:
        # Delete a specific memory
        result = await memory_delete(
            project_path="/projects/my-app",
            key="outdated-approach"
        )

        # Check if deletion succeeded
        if result["deleted"]:
            print(f"Deleted memory: {result['key']}")
        else:
            print("Memory not found")

    Use Cases:
        - Remove outdated or incorrect learnings
        - Clean up temporary memories
        - Correct mistakes in stored knowledge
        - Reduce memory store size

    Notes:
        - Deletion is permanent and cannot be undone
        - Returns success=True even if key doesn't exist
        - Use memory.list to verify before deleting
    """
    try:
        store = MemoryStore(Path(project_path))

        # Check if exists first
        existing = store.get(key)
        if not existing:
            return {
                "success": True,
                "key": key,
                "deleted": False,
                "message": f"Memory '{key}' not found"
            }

        # Delete memory
        deleted = store.delete(key)

        return {
            "success": True,
            "key": key,
            "deleted": deleted,
            "previous_value": existing.value[:100] + ("..." if len(existing.value) > 100 else ""),
            "previous_tags": existing.tags,
            "message": f"Memory '{key}' deleted successfully" if deleted else f"Memory '{key}' not found"
        }

    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to delete memory: {str(e)}"
        }
