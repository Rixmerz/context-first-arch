"""
MCP Tool: rule.batch

Batch confirm or reject multiple business rules at once.
"""

from typing import Any, Dict, List, Optional
from pathlib import Path

from src.features.knowledge_graph import (
    BusinessRuleStore,
    RuleStatus,
)


async def rule_batch(
    project_path: str,
    rule_ids: List[str],
    action: str,
    reason: Optional[str] = None
) -> Dict[str, Any]:
    """
    Batch confirm or reject multiple business rules.

    Args:
        project_path: Path to CFA project
        rule_ids: List of rule IDs to process
        action: "confirm" or "reject"
        reason: Optional reason (required for reject)

    Returns:
        Dictionary with:
            - success: Boolean
            - processed: Number of rules processed
            - results: Individual results for each rule
            - summary: Human-readable summary

    Examples:
        # Confirm multiple rules at once
        result = await rule_batch(
            project_path="/projects/my-app",
            rule_ids=["rule_abc", "rule_def", "rule_ghi"],
            action="confirm"
        )

        # Reject multiple non-business rules
        result = await rule_batch(
            project_path="/projects/my-app",
            rule_ids=["rule_xyz", "rule_uvw"],
            action="reject",
            reason="These are defensive programming checks, not business rules"
        )

    Best Practice:
        1. Use rule.list(pending_only=True) to get pending rules
        2. Review the batch_helper for suggested actions
        3. Use this tool to process multiple rules efficiently
    """
    try:
        path = Path(project_path)

        # Validate CFA project
        if not (path / ".claude").exists():
            return {
                "success": False,
                "error": "Not a CFA project (missing .claude/)"
            }

        # Validate action
        if action not in ("confirm", "reject"):
            return {
                "success": False,
                "error": f"Invalid action: {action}. Must be 'confirm' or 'reject'"
            }

        # Reject requires a reason
        if action == "reject" and not reason:
            return {
                "success": False,
                "error": "Rejection requires a reason"
            }

        rule_store = BusinessRuleStore(path)

        results = []
        successes = 0
        failures = 0

        for rule_id in rule_ids:
            try:
                if action == "confirm":
                    rule_store.confirm_rule(
                        rule_id=rule_id,
                        confirmed_by="batch_operation"
                    )
                    results.append({
                        "rule_id": rule_id,
                        "success": True,
                        "action": "confirmed"
                    })
                    successes += 1
                else:
                    rule_store.reject_rule(
                        rule_id=rule_id,
                        rejection_reason=reason
                    )
                    results.append({
                        "rule_id": rule_id,
                        "success": True,
                        "action": "rejected"
                    })
                    successes += 1

            except Exception as e:
                results.append({
                    "rule_id": rule_id,
                    "success": False,
                    "error": str(e)
                })
                failures += 1

        # Build summary
        summary = f"Processed {len(rule_ids)} rules: {successes} {action}ed"
        if failures > 0:
            summary += f", {failures} failed"

        return {
            "success": failures == 0,
            "processed": len(rule_ids),
            "successes": successes,
            "failures": failures,
            "results": results,
            "summary": summary,
            "message": summary,
        }

    except Exception as e:
        return {
            "success": False,
            "error": f"Batch operation failed: {str(e)}"
        }
