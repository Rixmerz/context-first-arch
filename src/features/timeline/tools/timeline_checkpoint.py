"""
MCP Tool: timeline.checkpoint

Create a snapshot of current project state.
"""

from typing import Any, Dict, List, Optional
from pathlib import Path

from src.features.knowledge_graph import (
    TimelineManager,
    SnapshotType,
)


async def timeline_checkpoint(
    project_path: str,
    name: str,
    description: Optional[str] = None,
    snapshot_type: str = "user",
    tags: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Create a checkpoint (snapshot) of current project state.

    Use this BEFORE risky operations to create a restore point.
    Two types of snapshots:
    - "user": Manual checkpoints (recommended before big changes)
    - "agent": Automatic AI checkpoints during work

    Args:
        project_path: Path to CFA project
        name: Short name for the checkpoint (e.g., "before-refactor")
        description: Longer description of what this checkpoint captures
        snapshot_type: "user" (manual) or "agent" (automatic)
        tags: Optional tags for categorization

    Returns:
        Dictionary with:
            - success: Boolean
            - snapshot: Created snapshot details
            - summary: Human-readable summary

    Examples:
        # Create checkpoint before refactoring
        result = await timeline_checkpoint(
            project_path="/projects/my-app",
            name="before-auth-refactor",
            description="State before refactoring authentication module",
            tags=["refactor", "auth"]
        )

        # Agent auto-checkpoint
        result = await timeline_checkpoint(
            project_path="/projects/my-app",
            name="task-123-midpoint",
            description="Checkpoint after completing step 3 of task",
            snapshot_type="agent"
        )

    Best Practice:
        1. Create checkpoints before risky operations
        2. Use descriptive names ("before-X", "after-Y")
        3. Use tags for easy filtering
        4. If something goes wrong, use timeline.rollback
    """
    try:
        path = Path(project_path)

        # Validate CFA project
        if not (path / ".claude").exists():
            return {
                "success": False,
                "error": "Not a CFA project (missing .claude/)"
            }

        # Validate snapshot type
        try:
            snap_type = SnapshotType(snapshot_type)
        except ValueError:
            return {
                "success": False,
                "error": f"Invalid snapshot_type: {snapshot_type}. Must be 'user' or 'agent'"
            }

        timeline = TimelineManager(path)

        # Create snapshot
        snapshot = timeline.create_snapshot(
            name=name,
            description=description or f"Checkpoint: {name}",
            snapshot_type=snap_type,
            created_by="user" if snap_type == SnapshotType.USER else "agent",
            tags=tags,
        )

        # Build response
        return {
            "success": True,
            "snapshot": {
                "id": snapshot.id,
                "name": snapshot.name,
                "type": snapshot.snapshot_type.value,
                "description": snapshot.description,
                "git_commit": snapshot.git_commit[:8] if snapshot.git_commit else None,
                "git_branch": snapshot.git_branch,
                "git_dirty": snapshot.git_dirty,
                "file_count": len(snapshot.files),
                "created_at": snapshot.created_at.isoformat(),
                "previous_snapshot": snapshot.previous_snapshot_id,
                "tags": snapshot.tags,
            },
            "summary": (
                f"Created checkpoint '{name}' ({snapshot.id}) with "
                f"{len(snapshot.files)} files tracked"
            ),
            "message": f"Checkpoint '{name}' created successfully",
            "tip": f"Use timeline.rollback(snapshot_id='{snapshot.id}') to restore this state"
        }

    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to create checkpoint: {str(e)}"
        }
