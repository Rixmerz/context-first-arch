"""
MCP Tool: memory.edit

Edit an existing memory.
"""

from typing import Any, Dict, List, Optional
from pathlib import Path

from src.core.memory_store import MemoryStore


async def memory_edit(
    project_path: str,
    key: str,
    new_value: Optional[str] = None,
    new_tags: Optional[List[str]] = None,
    append: bool = False
) -> Dict[str, Any]:
    """
    Edit an existing memory.

    Updates the value and/or tags of an existing memory.
    Supports both replacement and append modes.

    Args:
        project_path: Path to the project root
        key: Memory identifier to edit
        new_value: New content (replaces or appends based on append flag)
        new_tags: New tags (completely replaces existing tags)
        append: If True, append new_value to existing value

    Returns:
        Dictionary with:
            - success: Boolean
            - key: Memory key
            - previous_value: Previous content (truncated)
            - new_value: Updated content (truncated)
            - tags: Updated tags
            - timestamp: New timestamp

    Example:
        # Replace memory value
        result = await memory_edit(
            project_path="/projects/my-app",
            key="auth-approach",
            new_value="Using JWT with refresh tokens stored in httpOnly cookies"
        )

        # Append to existing memory
        result = await memory_edit(
            project_path="/projects/my-app",
            key="learned-patterns",
            new_value="- Also uses repository pattern for data access",
            append=True
        )

        # Update tags only
        result = await memory_edit(
            project_path="/projects/my-app",
            key="database-schema",
            new_tags=["database", "schema", "important"]
        )

    Notes:
        - At least one of new_value or new_tags must be provided
        - append=True only affects new_value, not tags
        - Tags are always replaced entirely, not merged
    """
    try:
        if new_value is None and new_tags is None:
            return {
                "success": False,
                "error": "Must provide new_value or new_tags to edit"
            }

        store = MemoryStore(Path(project_path))

        # Get previous value for comparison
        previous = store.get(key)
        if not previous:
            return {
                "success": False,
                "error": f"Memory not found: {key}"
            }

        # Edit memory
        updated = store.edit(
            key=key,
            new_value=new_value,
            new_tags=new_tags,
            append=append
        )

        if not updated:
            return {
                "success": False,
                "error": f"Failed to edit memory: {key}"
            }

        return {
            "success": True,
            "key": key,
            "previous_value": previous.value[:200] + ("..." if len(previous.value) > 200 else ""),
            "new_value": updated.value[:200] + ("..." if len(updated.value) > 200 else ""),
            "previous_tags": previous.tags,
            "new_tags": updated.tags,
            "timestamp": updated.timestamp,
            "mode": "append" if append else "replace",
            "message": f"Memory '{key}' updated successfully"
        }

    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to edit memory: {str(e)}"
        }
