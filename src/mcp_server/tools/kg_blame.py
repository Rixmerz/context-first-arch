"""
MCP Tool: kg.blame

Show who last modified a node in the Knowledge Graph.
"""

from typing import Any, Dict, Optional


async def kg_blame(
    node_id: str,
    project_path: Optional[str] = None
) -> Dict[str, Any]:
    """
    Show who last modified a node.

    Args:
        node_id: Node identifier
        project_path: Optional CFA project path

    Returns:
        Dictionary with blame information
    """
    return {
        "success": True,
        "node_id": node_id,
        "author": None,
        "timestamp": None,
        "message": "Blame information not available"
    }
