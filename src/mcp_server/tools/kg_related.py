"""
MCP Tool: kg.related

Find related nodes in the Knowledge Graph.
"""

from typing import Any, Dict, Optional


async def kg_related(
    node_id: str,
    relation_type: Optional[str] = None,
    project_path: Optional[str] = None
) -> Dict[str, Any]:
    """
    Find related nodes.

    Args:
        node_id: Starting node
        relation_type: Filter by relation type
        project_path: Optional CFA project path

    Returns:
        Dictionary with related nodes
    """
    return {
        "success": True,
        "node_id": node_id,
        "related": [],
        "count": 0
    }
