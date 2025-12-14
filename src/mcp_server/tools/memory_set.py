"""
MCP Tool: memory.set

[PRIMARY] Store project learnings in persistent memory.
Consolidates: memory.set + memory.edit
"""

from typing import Any, Dict, List, Optional
from pathlib import Path

from src.core.memory_store import MemoryStore


async def memory_set(
    project_path: str,
    key: str,
    value: str,
    tags: Optional[List[str]] = None,
    append: bool = False
) -> Dict[str, Any]:
    """
    [PRIMARY] Store or update a memory in project knowledge base.

    Memories persist in SQLite across sessions. Use for storing:
    - Architectural decisions and rationale
    - Lessons learned during development
    - Code patterns and conventions
    - Important context for future sessions

    Args:
        project_path: Path to CFA project
        key: Unique identifier for the memory
        value: Content to store
        tags: Optional list of tags for categorization
        append: If True and key exists, append value instead of replace

    Returns:
        Dictionary with:
            - success: Boolean
            - key: Memory key
            - timestamp: When memory was stored
            - tags: Applied tags
            - mode: "create", "replace", or "append"
            - previous_value: (only if updating) Previous content preview

    Examples:
        # Create new memory
        result = await memory_set(
            project_path="/projects/my-app",
            key="auth-decision",
            value="Using JWT for stateless authentication",
            tags=["architecture", "security"]
        )

        # Update existing memory (replace)
        result = await memory_set(
            project_path="/projects/my-app",
            key="auth-decision",
            value="Switched to session-based auth for security",
            tags=["architecture", "security"]
        )

        # Append to existing memory
        result = await memory_set(
            project_path="/projects/my-app",
            key="learned-patterns",
            value="\\n- Also uses repository pattern",
            append=True
        )

    Best Practice:
        Store insights after significant discoveries or decisions.
        Use consistent key naming: "topic-subtopic" format.
        Tag memories for easier retrieval with memory.search.
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

        # Initialize store
        store = MemoryStore(path)
        key = key.strip()
        value = value.strip()
        tags = tags or []

        # Check if memory exists
        existing = store.get(key)

        if existing and append:
            # Append mode - use edit with append
            updated = store.edit(
                key=key,
                new_value=value,
                new_tags=tags if tags else None,
                append=True
            )

            if not updated:
                return {
                    "success": False,
                    "error": f"Failed to append to memory: {key}"
                }

            return {
                "success": True,
                "key": updated.key,
                "timestamp": updated.timestamp,
                "tags": updated.tags,
                "mode": "append",
                "previous_value": existing.value[:200] + ("..." if len(existing.value) > 200 else ""),
                "new_value": updated.value[:200] + ("..." if len(updated.value) > 200 else ""),
                "message": f"Appended to memory '{key}'"
            }

        elif existing:
            # Replace mode - update existing
            updated = store.edit(
                key=key,
                new_value=value,
                new_tags=tags if tags else None,
                append=False
            )

            if not updated:
                return {
                    "success": False,
                    "error": f"Failed to update memory: {key}"
                }

            return {
                "success": True,
                "key": updated.key,
                "timestamp": updated.timestamp,
                "tags": updated.tags,
                "mode": "replace",
                "previous_value": existing.value[:200] + ("..." if len(existing.value) > 200 else ""),
                "message": f"Updated memory '{key}'" + (f" with tags: {', '.join(updated.tags)}" if updated.tags else "")
            }

        else:
            # Create new memory
            memory = store.set(key=key, value=value, tags=tags)

            return {
                "success": True,
                "key": memory.key,
                "timestamp": memory.timestamp,
                "tags": memory.tags,
                "mode": "create",
                "message": f"Created memory '{key}'" + (f" with tags: {', '.join(memory.tags)}" if memory.tags else "")
            }

    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to store memory: {str(e)}"
        }
