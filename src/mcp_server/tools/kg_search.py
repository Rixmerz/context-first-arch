"""
MCP Tool: kg.search

Search the Knowledge Graph.
"""

from typing import Any, Dict, Optional


async def kg_search(
    query: str,
    node_type: Optional[str] = None,
    limit: int = 10,
    project_path: Optional[str] = None
) -> Dict[str, Any]:
    """
    Search the Knowledge Graph.

    Args:
        query: Search query
        node_type: Filter by node type
        limit: Maximum results
        project_path: Optional CFA project path

    Returns:
        Dictionary with search results
    """
    return {
        "success": True,
        "query": query,
        "results": [],
        "count": 0
    }
