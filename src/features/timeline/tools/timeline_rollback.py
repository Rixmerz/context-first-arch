"""
MCP Tool: timeline.rollback

Return to a previous snapshot state.
"""

from typing import Any, Dict, Optional
from pathlib import Path
import subprocess

from src.features.knowledge_graph import TimelineManager


async def timeline_rollback(
    project_path: str,
    snapshot_id: str,
    mode: str = "preview",
    include_git: bool = False
) -> Dict[str, Any]:
    """
    Return to a previous snapshot state.

    CAUTION: This can modify or delete files!

    Args:
        project_path: Path to CFA project
        snapshot_id: ID of snapshot to rollback to
        mode: "preview" (show what would change) or "execute" (actually rollback)
        include_git: Also reset git to snapshot's commit (dangerous!)

    Returns:
        Dictionary with:
            - success: Boolean
            - changes: What would/did change
            - summary: Human-readable summary

    Examples:
        # Preview what would change
        result = await timeline_rollback(
            project_path="/projects/my-app",
            snapshot_id="abc123",
            mode="preview"
        )

        # Actually rollback
        result = await timeline_rollback(
            project_path="/projects/my-app",
            snapshot_id="abc123",
            mode="execute"
        )

    IMPORTANT - Safety:
        1. Always preview first!
        2. This creates a new checkpoint before executing
        3. Git rollback is separate and optional (and dangerous)
        4. Cannot rollback file content - only detects changes
    """
    try:
        path = Path(project_path)

        # Validate CFA project
        if not (path / ".claude").exists():
            return {
                "success": False,
                "error": "Not a CFA project (missing .claude/)"
            }

        # Validate mode
        if mode not in ["preview", "execute"]:
            return {
                "success": False,
                "error": f"Invalid mode: {mode}. Must be 'preview' or 'execute'"
            }

        timeline = TimelineManager(path)

        # Get target snapshot
        target = timeline.get_snapshot(snapshot_id)
        if not target:
            return {
                "success": False,
                "error": f"Snapshot not found: {snapshot_id}"
            }

        # Get current state for comparison
        current_snapshot = timeline.create_snapshot(
            name=f"before-rollback-{snapshot_id[:8]}",
            description=f"Auto-checkpoint before rollback to {target.name}",
            snapshot_type=target.snapshot_type,
            created_by="system",
            tags=["auto", "pre-rollback"],
        )

        # Compare states
        comparison = timeline.compare_snapshots(
            snapshot_a_id=current_snapshot.id,
            snapshot_b_id=snapshot_id
        )

        if mode == "preview":
            return {
                "success": True,
                "mode": "preview",
                "target_snapshot": {
                    "id": target.id,
                    "name": target.name,
                    "created_at": target.created_at.isoformat(),
                    "git_commit": target.git_commit[:8] if target.git_commit else None,
                },
                "changes": {
                    "files_to_restore": comparison["removed"],  # Were in target, not in current
                    "files_to_remove": comparison["added"],     # In current, not in target
                    "files_modified": comparison["modified"],   # Changed since target
                },
                "change_count": (
                    len(comparison["removed"]) +
                    len(comparison["added"]) +
                    len(comparison["modified"])
                ),
                "summary": comparison["summary"],
                "message": (
                    f"Preview: Rollback would affect "
                    f"{len(comparison['removed']) + len(comparison['added']) + len(comparison['modified'])} files"
                ),
                "warning": (
                    "This is a preview. Use mode='execute' to actually rollback. "
                    "Note: CFA cannot restore file content - use git for full restoration."
                ),
                "pre_rollback_checkpoint": current_snapshot.id,
            }

        # Execute mode
        # Note: CFA tracks state but doesn't store full file content
        # Full rollback requires git
        git_result = None
        if include_git and target.git_commit:
            try:
                # This is dangerous - only do if explicitly requested
                proc = subprocess.run(
                    ["git", "checkout", target.git_commit],
                    capture_output=True, text=True,
                    cwd=project_path
                )
                git_result = {
                    "success": proc.returncode == 0,
                    "message": proc.stdout or proc.stderr,
                }
            except Exception as e:
                git_result = {
                    "success": False,
                    "message": str(e),
                }

        return {
            "success": True,
            "mode": "execute",
            "target_snapshot": {
                "id": target.id,
                "name": target.name,
                "created_at": target.created_at.isoformat(),
            },
            "changes_detected": {
                "files_in_target_not_current": comparison["removed"],
                "files_in_current_not_target": comparison["added"],
                "files_modified": comparison["modified"],
            },
            "git_rollback": git_result,
            "pre_rollback_checkpoint": current_snapshot.id,
            "summary": comparison["summary"],
            "message": (
                f"Rollback analysis complete. "
                f"{'Git restored to ' + target.git_commit[:8] if git_result and git_result['success'] else 'Use git checkout for full restoration'}"
            ),
            "tip": (
                f"To fully restore: git checkout {target.git_commit}"
                if target.git_commit and not (git_result and git_result.get("success"))
                else None
            ),
        }

    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to rollback: {str(e)}"
        }
