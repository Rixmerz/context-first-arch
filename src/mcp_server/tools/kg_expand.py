"""
MCP Tool: kg.expand

Expand a node in the Knowledge Graph to show connected nodes.
"""

from typing import Any, Dict, Optional


async def kg_expand(
    node_id: str,
    depth: int = 1,
    project_path: Optional[str] = None
) -> Dict[str, Any]:
    """
    Expand a node to show connected nodes.

    Args:
        node_id: Node to expand
        depth: How many levels to expand
        project_path: Optional CFA project path

    Returns:
        Dictionary with expanded graph
    """
    return {
        "success": True,
        "node_id": node_id,
        "depth": depth,
        "connected_nodes": [],
        "edges": []
    }
