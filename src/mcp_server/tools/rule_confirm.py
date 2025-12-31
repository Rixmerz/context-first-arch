"""
MCP Tool: rule.confirm

Confirm a rule application.
"""

from typing import Any, Dict, Optional


async def rule_confirm(
    rule_id: str,
    confirmed: bool = True,
    project_path: Optional[str] = None
) -> Dict[str, Any]:
    """
    Confirm a rule application.

    Args:
        rule_id: Rule to confirm
        confirmed: Whether to confirm
        project_path: Optional CFA project path

    Returns:
        Dictionary with confirmation result
    """
    return {
        "success": True,
        "rule_id": rule_id,
        "confirmed": confirmed,
        "message": f"Rule '{rule_id}' {'confirmed' if confirmed else 'rejected'}"
    }
