"""
MCP Tool: memory.search

Search project learnings in persistent memory.
"""

from typing import Any, Dict, List, Optional
from pathlib import Path

from src.features.memory import MemoryStore


async def memory_search(
    project_path: str,
    query: str = "",
    tags: Optional[List[str]] = None,
    limit: int = 50
) -> Dict[str, Any]:
    """
    Search memories by query and/or tags.

    Args:
        project_path: Path to CFA project
        query: Text to search in memory values (case-insensitive)
        tags: Optional list of tags to filter by (AND logic)
        limit: Maximum number of results (default: 50)

    Returns:
        Dictionary with:
            - success: Boolean
            - results: List of matching memories
            - count: Number of results
            - stats: Memory store statistics

    Example:
        # Search by query
        result = await memory_search(
            project_path="/projects/my-app",
            query="authentication"
        )

        # Search by tags
        result = await memory_search(
            project_path="/projects/my-app",
            tags=["architecture", "security"]
        )

        # Combined search
        result = await memory_search(
            project_path="/projects/my-app",
            query="JWT",
            tags=["auth"]
        )
    """
    try:
        path = Path(project_path)

        # Validate CFA project
        if not (path / ".claude").exists():
            return {"success": False, "error": "Not a CFA project (missing .claude/)"}

        # Search memories
        store = MemoryStore(path)
        memories = store.search(query=query, tags=tags)

        # Apply limit
        limited_memories = memories[:limit]

        # Format results
        results = [
            {
                "key": m.key,
                "value": m.value,
                "timestamp": m.timestamp,
                "tags": m.tags
            }
            for m in limited_memories
        ]

        # Get stats
        stats = store.get_stats()

        return {
            "success": True,
            "results": results,
            "count": len(results),
            "total_matches": len(memories),
            "stats": stats,
            "message": _format_message(query, tags, len(results), len(memories))
        }

    except Exception as e:
        return {
            "success": False,
            "error": f"Memory search failed: {str(e)}"
        }


def _format_message(query: str, tags: Optional[List[str]], count: int, total: int) -> str:
    """Generate human-readable message."""
    search_parts = []

    if query:
        search_parts.append(f"query='{query}'")
    if tags:
        search_parts.append(f"tags={tags}")

    search_str = ", ".join(search_parts) if search_parts else "all memories"

    if count == 0:
        return f"No memories found for {search_str}"

    if count == total:
        return f"Found {count} memory/ies for {search_str}"
    else:
        return f"Found {count}/{total} memories for {search_str} (limited)"
