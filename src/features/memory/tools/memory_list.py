"""
MCP Tool: memory.list

List all stored memories.
"""

from typing import Any, Dict, List, Optional
from pathlib import Path

from src.features.memory import MemoryStore


async def memory_list(
    project_path: str,
    limit: int = 100,
    tags: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    List all stored memories for a project.

    Returns memories sorted by timestamp (most recent first)
    with optional filtering by tags.

    Args:
        project_path: Path to the project root
        limit: Maximum number of memories to return (default: 100)
        tags: Optional list of tags to filter by

    Returns:
        Dictionary with:
            - success: Boolean
            - memories: List of memories with:
                - key: Memory identifier
                - value: Memory content (truncated preview)
                - timestamp: When stored/updated
                - tags: List of tags
            - count: Number of memories returned
            - stats: Memory store statistics

    Example:
        # List all memories
        result = await memory_list(
            project_path="/projects/my-app"
        )

        # List recent memories with tag filter
        result = await memory_list(
            project_path="/projects/my-app",
            limit=20,
            tags=["architecture"]
        )

        # Show memory keys and previews
        for mem in result["memories"]:
            print(f"{mem['key']}: {mem['value'][:50]}...")

    Use Cases:
        - Review what the AI has learned about the project
        - Find specific memories by tag
        - Audit stored knowledge
        - Clean up outdated memories
    """
    try:
        store = MemoryStore(Path(project_path))

        if tags:
            # Use search with tag filter
            memories = store.search(query="", tags=tags)[:limit]
        else:
            memories = store.list_all(limit=limit)

        # Get stats
        stats = store.get_stats()

        # Format memories for output
        formatted = []
        for mem in memories:
            formatted.append({
                "key": mem.key,
                "value": mem.value[:200] + ("..." if len(mem.value) > 200 else ""),
                "timestamp": mem.timestamp,
                "tags": mem.tags
            })

        return {
            "success": True,
            "project_path": project_path,
            "memories": formatted,
            "count": len(formatted),
            "stats": stats
        }

    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to list memories: {str(e)}"
        }
