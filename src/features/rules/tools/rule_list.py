"""
MCP Tool: rule.list

List business rules with filtering and status.
"""

from typing import Any, Dict, List, Optional
from pathlib import Path

from src.features.knowledge_graph import (
    BusinessRuleStore,
    RuleStatus,
    RuleCategory,
)


async def rule_list(
    project_path: str,
    status: Optional[str] = None,
    category: Optional[str] = None,
    file_path: Optional[str] = None,
    chunk_id: Optional[str] = None,
    pending_only: bool = False,
    limit: int = 50
) -> Dict[str, Any]:
    """
    List business rules with optional filters.

    Args:
        project_path: Path to CFA project
        status: Filter by status (proposed, confirmed, corrected, rejected)
        category: Filter by category (validation, authorization, business_logic, etc.)
        file_path: Filter by source file
        chunk_id: Get rules for specific chunk
        pending_only: Only show rules awaiting confirmation
        limit: Maximum rules to return

    Returns:
        Dictionary with:
            - success: Boolean
            - rules: List of rules
            - stats: Statistics about rules
            - summary: Human-readable summary

    Examples:
        # List all pending rules
        result = await rule_list(
            project_path="/projects/my-app",
            pending_only=True
        )

        # List confirmed validation rules
        result = await rule_list(
            project_path="/projects/my-app",
            status="confirmed",
            category="validation"
        )

        # List rules for a specific file
        result = await rule_list(
            project_path="/projects/my-app",
            file_path="src/auth.py"
        )

    Best Practice:
        1. Start with pending_only=True to review proposed rules
        2. Use rule.confirm to confirm/reject each
        3. Use status="confirmed" to see your business knowledge base
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

        # Handle pending_only shortcut
        if pending_only:
            rules = rule_store.get_pending_rules()
        elif chunk_id:
            rules = rule_store.get_rules_for_chunk(chunk_id)
        else:
            # Convert string filters to enums
            status_filter = None
            if status:
                try:
                    status_filter = RuleStatus(status)
                except ValueError:
                    return {
                        "success": False,
                        "error": f"Invalid status: {status}. Valid: {[s.value for s in RuleStatus]}"
                    }

            category_filter = None
            if category:
                try:
                    category_filter = RuleCategory(category)
                except ValueError:
                    return {
                        "success": False,
                        "error": f"Invalid category: {category}. Valid: {[c.value for c in RuleCategory]}"
                    }

            rules = rule_store.list_rules(
                status=status_filter,
                category=category_filter,
                file_path=file_path,
                limit=limit
            )

        # Format rules for output with quick actions
        rule_list = []
        for rule in rules[:limit]:
            rule_data = {
                "id": rule.id,
                "rule_text": rule.human_correction or rule.rule_text,
                "category": rule.category.value,
                "status": rule.status.value,
                "confidence": f"{rule.confidence:.0%}",
                "source_file": rule.source_file,
                "source_symbol": rule.source_symbol,
                "source_lines": rule.source_lines,
                "confirmed_by": rule.confirmed_by,
                "created_at": rule.created_at.isoformat() if rule.created_at else None,
            }

            # Add quick actions for pending rules
            if rule.status == RuleStatus.PROPOSED:
                rule_data["quick_actions"] = {
                    "confirm": f'rule.confirm(project_path="{project_path}", rule_id="{rule.id}", action="confirm")',
                    "reject": f'rule.confirm(project_path="{project_path}", rule_id="{rule.id}", action="reject", rejection_reason="<reason>")',
                    "correct": f'rule.confirm(project_path="{project_path}", rule_id="{rule.id}", action="correct", correction="<corrected text>")',
                }

            rule_list.append(rule_data)

        # Calculate stats
        stats = {
            "total": len(rules),
            "by_status": {},
            "by_category": {},
        }

        for rule in rules:
            status_val = rule.status.value
            stats["by_status"][status_val] = stats["by_status"].get(status_val, 0) + 1

            cat_val = rule.category.value
            stats["by_category"][cat_val] = stats["by_category"].get(cat_val, 0) + 1

        # Build summary
        pending = stats["by_status"].get("proposed", 0)
        confirmed = stats["by_status"].get("confirmed", 0) + stats["by_status"].get("corrected", 0)

        summary = f"{len(rules)} business rules found"
        if pending:
            summary += f" ({pending} pending review)"
        if confirmed:
            summary += f" ({confirmed} confirmed)"

        # Build pending review section for easy workflow
        pending_review = [
            r for r in rule_list
            if r.get("status") == "proposed"
        ]

        # Build batch confirm helper for pending rules
        batch_helper = None
        if pending_review:
            pending_ids = [r["id"] for r in pending_review]
            batch_helper = {
                "confirm_all": f'# Confirm all {len(pending_ids)} pending rules:\n' +
                    '\n'.join([f'rule.confirm(project_path="{project_path}", rule_id="{rid}", action="confirm")' for rid in pending_ids[:5]]) +
                    (f'\n# ... and {len(pending_ids) - 5} more' if len(pending_ids) > 5 else ''),
                "ids": pending_ids,
                "count": len(pending_ids),
            }

        return {
            "success": True,
            # Summary at top
            "summary": {
                "total": len(rules),
                "pending": pending,
                "confirmed": confirmed,
                "by_status": stats["by_status"],
                "by_category": stats["by_category"],
            },
            # Pending review section for easy workflow
            "pending_review": pending_review[:10] if pending_review else [],
            "pending_count": len(pending_review),
            # Batch operations helper
            "batch_helper": batch_helper,
            # Full rules list
            "rules": rule_list,
            "count": len(rule_list),
            "filters": {
                "status": status,
                "category": category,
                "file_path": file_path,
                "chunk_id": chunk_id,
                "pending_only": pending_only,
            },
            "message": summary,
        }

    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to list rules: {str(e)}"
        }
