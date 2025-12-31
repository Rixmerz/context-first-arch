"""
MCP Tool: rule.list

List available rules.
"""

from typing import Any, Dict, Optional


async def rule_list(
    category: Optional[str] = None,
    project_path: Optional[str] = None
) -> Dict[str, Any]:
    """
    List available rules.

    Args:
        category: Filter by category
        project_path: Optional CFA project path

    Returns:
        Dictionary with rules list
    """
    return {
        "success": True,
        "rules": [],
        "count": 0,
        "filter": {"category": category} if category else None
    }
