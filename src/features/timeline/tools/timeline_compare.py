"""
MCP Tool: timeline.compare

Compare two snapshots to see what changed.
"""

from typing import Any, Dict, List, Optional
from pathlib import Path

from src.features.knowledge_graph import TimelineManager, SnapshotType


async def timeline_compare(
    project_path: str,
    snapshot_a: Optional[str] = None,
    snapshot_b: Optional[str] = None,
    include_details: bool = False
) -> Dict[str, Any]:
    """
    Compare two snapshots to see what changed between them.

    Args:
        project_path: Path to CFA project
        snapshot_a: First snapshot ID (older). If None, uses earliest.
        snapshot_b: Second snapshot ID (newer). If None, uses current state.
        include_details: Include file-level details

    Returns:
        Dictionary with:
            - success: Boolean
            - comparison: What changed between snapshots
            - summary: Human-readable summary

    Examples:
        # Compare two specific snapshots
        result = await timeline_compare(
            project_path="/projects/my-app",
            snapshot_a="abc123",
            snapshot_b="def456"
        )

        # Compare snapshot to current state
        result = await timeline_compare(
            project_path="/projects/my-app",
            snapshot_a="abc123"  # snapshot_b defaults to current
        )

        # Get all snapshots to pick from
        result = await timeline_compare(
            project_path="/projects/my-app"
            # Returns list of available snapshots when neither is specified
        )

    Best Practice:
        Use this to understand:
        1. What changed during a work session
        2. Impact of a refactoring
        3. Drift from a known-good state
    """
    try:
        path = Path(project_path)

        # Validate CFA project
        if not (path / ".claude").exists():
            return {
                "success": False,
                "error": "Not a CFA project (missing .claude/)"
            }

        timeline = TimelineManager(path)

        # If no snapshots specified, list available ones
        if not snapshot_a and not snapshot_b:
            snapshots = timeline.list_snapshots(limit=20)
            return {
                "success": True,
                "mode": "list",
                "available_snapshots": [
                    {
                        "id": s.id,
                        "name": s.name,
                        "type": s.snapshot_type.value,
                        "created_at": s.created_at.isoformat(),
                        "file_count": len(s.files),
                        "git_commit": s.git_commit[:8] if s.git_commit else None,
                    }
                    for s in snapshots
                ],
                "count": len(snapshots),
                "message": f"Found {len(snapshots)} snapshots. Specify snapshot_a and snapshot_b to compare.",
            }

        # If only snapshot_a, compare to current state
        if snapshot_a and not snapshot_b:
            # Create temp snapshot of current state
            current = timeline.create_snapshot(
                name="current-state-temp",
                description="Temporary snapshot for comparison",
                snapshot_type=SnapshotType.AGENT,
                created_by="system",
                tags=["temp", "comparison"],
            )
            snapshot_b = current.id

        # Get both snapshots
        snap_a = timeline.get_snapshot(snapshot_a)
        snap_b = timeline.get_snapshot(snapshot_b)

        if not snap_a:
            return {
                "success": False,
                "error": f"Snapshot not found: {snapshot_a}"
            }
        if not snap_b:
            return {
                "success": False,
                "error": f"Snapshot not found: {snapshot_b}"
            }

        # Compare
        comparison = timeline.compare_snapshots(snapshot_a, snapshot_b)

        # Build response
        result = {
            "success": True,
            "mode": "compare",
            "snapshot_a": {
                "id": snap_a.id,
                "name": snap_a.name,
                "type": snap_a.snapshot_type.value,
                "created_at": snap_a.created_at.isoformat(),
                "file_count": len(snap_a.files),
                "git_commit": snap_a.git_commit[:8] if snap_a.git_commit else None,
            },
            "snapshot_b": {
                "id": snap_b.id,
                "name": snap_b.name,
                "type": snap_b.snapshot_type.value,
                "created_at": snap_b.created_at.isoformat(),
                "file_count": len(snap_b.files),
                "git_commit": snap_b.git_commit[:8] if snap_b.git_commit else None,
            },
            "changes": {
                "added": len(comparison["added"]),
                "removed": len(comparison["removed"]),
                "modified": len(comparison["modified"]),
                "unchanged": comparison["unchanged_count"],
            },
            "summary": comparison["summary"],
            "message": (
                f"Comparing '{snap_a.name}' → '{snap_b.name}': "
                f"{comparison['summary']}"
            ),
        }

        if include_details:
            result["files"] = {
                "added": comparison["added"][:50],
                "removed": comparison["removed"][:50],
                "modified": comparison["modified"][:50],
            }
            if len(comparison["added"]) > 50:
                result["files"]["added_truncated"] = len(comparison["added"]) - 50
            if len(comparison["removed"]) > 50:
                result["files"]["removed_truncated"] = len(comparison["removed"]) - 50
            if len(comparison["modified"]) > 50:
                result["files"]["modified_truncated"] = len(comparison["modified"]) - 50

        return result

    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to compare snapshots: {str(e)}"
        }


async def timeline_list(
    project_path: str,
    snapshot_type: Optional[str] = None,
    limit: int = 20
) -> Dict[str, Any]:
    """
    List all snapshots in the timeline.

    Args:
        project_path: Path to CFA project
        snapshot_type: Filter by type ("user" or "agent")
        limit: Maximum snapshots to return

    Returns:
        Dictionary with list of snapshots
    """
    try:
        path = Path(project_path)

        if not (path / ".claude").exists():
            return {
                "success": False,
                "error": "Not a CFA project (missing .claude/)"
            }

        timeline = TimelineManager(path)

        # Convert type filter
        type_filter = None
        if snapshot_type:
            try:
                type_filter = SnapshotType(snapshot_type)
            except ValueError:
                return {
                    "success": False,
                    "error": f"Invalid snapshot_type: {snapshot_type}"
                }

        snapshots = timeline.list_snapshots(
            snapshot_type=type_filter,
            limit=limit
        )

        return {
            "success": True,
            "snapshots": [
                {
                    "id": s.id,
                    "name": s.name,
                    "type": s.snapshot_type.value,
                    "description": s.description[:100] + "..." if len(s.description) > 100 else s.description,
                    "created_at": s.created_at.isoformat(),
                    "created_by": s.created_by,
                    "file_count": len(s.files),
                    "git_commit": s.git_commit[:8] if s.git_commit else None,
                    "git_branch": s.git_branch,
                    "tags": s.tags,
                }
                for s in snapshots
            ],
            "count": len(snapshots),
            "summary": f"Found {len(snapshots)} snapshots",
        }

    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to list snapshots: {str(e)}"
        }
