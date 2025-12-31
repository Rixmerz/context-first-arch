"""
MCP Tool: kg.omitted

Show omitted nodes from the Knowledge Graph.
"""

from typing import Any, Dict, Optional


async def kg_omitted(
    project_path: Optional[str] = None
) -> Dict[str, Any]:
    """
    Show omitted nodes from the Knowledge Graph.

    Args:
        project_path: Optional CFA project path

    Returns:
        Dictionary with omitted nodes
    """
    return {
        "success": True,
        "omitted_nodes": [],
        "count": 0,
        "message": "No omitted nodes"
    }
