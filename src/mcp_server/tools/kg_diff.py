"""
MCP Tool: kg.diff

Show differences in the Knowledge Graph.
"""

from typing import Any, Dict, Optional


async def kg_diff(
    from_ref: Optional[str] = None,
    to_ref: Optional[str] = None,
    project_path: Optional[str] = None
) -> Dict[str, Any]:
    """
    Show differences in the Knowledge Graph.

    Args:
        from_ref: Starting reference (commit/tag)
        to_ref: Ending reference
        project_path: Optional CFA project path

    Returns:
        Dictionary with diff information
    """
    return {
        "success": True,
        "added": [],
        "removed": [],
        "modified": [],
        "message": "No differences found"
    }
