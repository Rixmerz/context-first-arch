"""
MCP Tool: decision.add

Document an architecture decision.
"""

from typing import Any, Dict, List, Optional
from pathlib import Path
from datetime import datetime


async def decision_add(
    project_path: str,
    title: str,
    context: str,
    decision: str,
    reason: str,
    options_considered: Optional[List[str]] = None,
    consequences: Optional[str] = None
) -> Dict[str, Any]:
    """
    Add an architecture decision record to decisions.md.

    Documents the WHY behind technical choices for future reference.
    Essential for maintaining project understanding over time.

    Args:
        project_path: Path to CFA project
        title: Short title for the decision
        context: What situation led to this decision
        decision: What was decided
        reason: Why this option was chosen
        options_considered: Optional list of alternatives evaluated
        consequences: What this decision means for the project

    Returns:
        Dictionary with:
            - success: Boolean
            - entry: The decision entry that was added
            - message: Human-readable status

    Example:
        result = await decision_add(
            project_path="/projects/my-app",
            title="Use Zustand instead of Redux",
            context="Needed state management for user session",
            decision="Zustand",
            reason="Less boilerplate, simpler mental model, good TS support",
            options_considered=["Redux", "Zustand", "Jotai", "Context API"],
            consequences="Team needs to learn Zustand patterns"
        )
    """
    try:
        decisions_file = Path(project_path) / ".claude" / "decisions.md"

        if not decisions_file.exists():
            return {
                "success": False,
                "error": f"Not a CFA project: {project_path}"
            }

        # Build the decision entry
        date = datetime.now().strftime("%Y-%m-%d")
        entry_lines = [
            f"\n## {date}: {title}",
            f"**Context**: {context}",
        ]

        if options_considered:
            entry_lines.append(f"**Options considered**: {', '.join(options_considered)}")

        entry_lines.extend([
            f"**Decision**: {decision}",
            f"**Reason**: {reason}",
        ])

        if consequences:
            entry_lines.append(f"**Consequences**: {consequences}")

        entry = "\n".join(entry_lines) + "\n"

        # Append to decisions.md
        current_content = decisions_file.read_text()
        decisions_file.write_text(current_content + entry)

        return {
            "success": True,
            "entry": {
                "date": date,
                "title": title,
                "decision": decision
            },
            "file_updated": ".claude/decisions.md",
            "message": f"Decision documented: {title}"
        }

    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to add decision: {str(e)}"
        }
