"""
MCP Tool: kg.get

Get a specific node from the Knowledge Graph.
"""

from typing import Any, Dict, Optional


async def kg_get(
    node_id: str,
    project_path: Optional[str] = None
) -> Dict[str, Any]:
    """
    Get a specific node from the Knowledge Graph.

    Args:
        node_id: Node identifier
        project_path: Optional CFA project path

    Returns:
        Dictionary with node data
    """
    return {
        "success": True,
        "node_id": node_id,
        "node": None,
        "message": "Node not found"
    }
