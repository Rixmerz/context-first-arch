"""
MCP Tool: kg.status

Get Knowledge Graph status.
"""

from typing import Any, Dict, Optional


async def kg_status(
    project_path: Optional[str] = None
) -> Dict[str, Any]:
    """
    Get Knowledge Graph status.

    Args:
        project_path: Optional CFA project path

    Returns:
        Dictionary with KG status
    """
    return {
        "success": True,
        "status": "not_initialized",
        "node_count": 0,
        "edge_count": 0,
        "last_build": None
    }
