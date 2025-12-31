"""
MCP Tool: kg.history

Show history of changes to a node in the Knowledge Graph.
"""

from typing import Any, Dict, List, Optional


async def kg_history(
    node_id: str,
    limit: int = 10,
    project_path: Optional[str] = None
) -> Dict[str, Any]:
    """
    Show history of changes to a node.

    Args:
        node_id: Node identifier
        limit: Maximum entries to return
        project_path: Optional CFA project path

    Returns:
        Dictionary with history
    """
    return {
        "success": True,
        "node_id": node_id,
        "history": [],
        "count": 0
    }
