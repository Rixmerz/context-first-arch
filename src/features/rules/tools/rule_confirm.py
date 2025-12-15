"""
MCP Tool: rule.confirm

Human confirms, corrects, or rejects proposed business rules.
This is the critical human-in-the-loop step.
"""

from typing import Any, Dict, List, Optional
from pathlib import Path

from src.features.knowledge_graph import (
    BusinessRuleStore,
    RuleStatus,
)


async def rule_confirm(
    project_path: str,
    rule_id: str,
    action: str = "confirm",
    correction: Optional[str] = None,
    rejection_reason: Optional[str] = None,
    confirmed_by: str = "human"
) -> Dict[str, Any]:
    """
    Confirm, correct, or reject a proposed business rule.

    This is the CRITICAL human-in-the-loop step that validates
    AI-interpreted rules. Only confirmed rules become part of
    the project's business knowledge.

    Args:
        project_path: Path to CFA project
        rule_id: ID of the rule to act on
        action: One of "confirm", "correct", "reject"
        correction: If action=correct, the corrected rule text
        rejection_reason: If action=reject, why it was rejected
        confirmed_by: Who is confirming (default "human")

    Returns:
        Dictionary with:
            - success: Boolean
            - rule: Updated rule details
            - message: Confirmation message

    Examples:
        # Confirm a rule as accurate
        result = await rule_confirm(
            project_path="/projects/my-app",
            rule_id="abc123",
            action="confirm"
        )

        # Correct a rule
        result = await rule_confirm(
            project_path="/projects/my-app",
            rule_id="abc123",
            action="correct",
            correction="Users must be authenticated AND have admin role"
        )

        # Reject an inaccurate rule
        result = await rule_confirm(
            project_path="/projects/my-app",
            rule_id="abc123",
            action="reject",
            rejection_reason="This is just a debug check, not a business rule"
        )

    IMPORTANT - Why This Matters:
        Business rules capture tacit knowledge that isn't in code.
        Human confirmation ensures this knowledge is ACCURATE.
        Confirmed rules become trusted documentation.
    """
    try:
        path = Path(project_path)

        # Validate CFA project
        if not (path / ".claude").exists():
            return {
                "success": False,
                "error": "Not a CFA project (missing .claude/)"
            }

        rule_store = BusinessRuleStore(path)

        # Get the rule
        rule = rule_store.get_rule(rule_id)
        if not rule:
            return {
                "success": False,
                "error": f"Rule not found: {rule_id}"
            }

        # Validate action
        valid_actions = ["confirm", "correct", "reject"]
        if action not in valid_actions:
            return {
                "success": False,
                "error": f"Invalid action: {action}. Must be one of {valid_actions}"
            }

        # Perform action
        if action == "confirm":
            updated_rule = rule_store.confirm_rule(
                rule_id=rule_id,
                confirmed_by=confirmed_by
            )
            message = f"Rule '{rule_id}' confirmed as accurate business knowledge."

        elif action == "correct":
            if not correction:
                return {
                    "success": False,
                    "error": "Correction text is required for action='correct'"
                }
            updated_rule = rule_store.confirm_rule(
                rule_id=rule_id,
                confirmed_by=confirmed_by,
                correction=correction
            )
            message = f"Rule '{rule_id}' corrected and saved."

        elif action == "reject":
            if not rejection_reason:
                return {
                    "success": False,
                    "error": "Rejection reason is required for action='reject'"
                }
            updated_rule = rule_store.reject_rule(
                rule_id=rule_id,
                reason=rejection_reason,
                rejected_by=confirmed_by
            )
            message = f"Rule '{rule_id}' rejected: {rejection_reason}"

        if not updated_rule:
            return {
                "success": False,
                "error": f"Failed to update rule: {rule_id}"
            }

        return {
            "success": True,
            "rule": {
                "id": updated_rule.id,
                "rule_text": updated_rule.human_correction or updated_rule.rule_text,
                "category": updated_rule.category.value,
                "status": updated_rule.status.value,
                "source_file": updated_rule.source_file,
                "source_symbol": updated_rule.source_symbol,
                "confirmed_by": updated_rule.confirmed_by,
                "confirmed_at": updated_rule.confirmed_at.isoformat() if updated_rule.confirmed_at else None,
            },
            "action": action,
            "message": message,
        }

    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to confirm rule: {str(e)}"
        }


async def rule_confirm_batch(
    project_path: str,
    confirmations: List[Dict[str, Any]],
    confirmed_by: str = "human"
) -> Dict[str, Any]:
    """
    Batch confirm/reject multiple rules at once.

    Args:
        project_path: Path to CFA project
        confirmations: List of {rule_id, action, correction?, rejection_reason?}
        confirmed_by: Who is confirming

    Returns:
        Dictionary with results for each rule
    """
    results = []
    for conf in confirmations:
        result = await rule_confirm(
            project_path=project_path,
            rule_id=conf.get("rule_id", ""),
            action=conf.get("action", "confirm"),
            correction=conf.get("correction"),
            rejection_reason=conf.get("rejection_reason"),
            confirmed_by=confirmed_by
        )
        results.append({
            "rule_id": conf.get("rule_id"),
            "success": result.get("success", False),
            "message": result.get("message") or result.get("error")
        })

    successful = sum(1 for r in results if r["success"])
    return {
        "success": True,
        "results": results,
        "summary": f"Processed {len(results)} rules: {successful} successful"
    }
