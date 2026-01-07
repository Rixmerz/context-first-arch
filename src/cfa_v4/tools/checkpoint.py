"""
cfa.checkpoint - Simple git-based safe points.

Creates commits with prefix [CFA-SAFE] for easy identification.
Allows listing and rolling back to previous checkpoints.

No fancy orchestration. Just git.
"""

import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


def _run_git(project_path: str, args: List[str], check: bool = True) -> subprocess.CompletedProcess:
    """Run a git command in the project directory."""
    return subprocess.run(
        ["git"] + args,
        cwd=project_path,
        capture_output=True,
        text=True,
        check=check
    )


def _is_git_repo(project_path: str) -> bool:
    """Check if project is a git repository."""
    try:
        result = _run_git(project_path, ["rev-parse", "--git-dir"], check=False)
        return result.returncode == 0
    except Exception:
        return False


async def cfa_checkpoint(
    project_path: str,
    action: str = "create",
    message: Optional[str] = None,
    checkpoint_id: Optional[str] = None,
    include_untracked: bool = True,
    dry_run: bool = False
) -> Dict[str, Any]:
    """
    Manage git checkpoints for safe rollback.

    Args:
        project_path: Path to project root
        action: "create" | "list" | "rollback"
        message: Description for the checkpoint (required for create)
        checkpoint_id: Commit hash to rollback to (required for rollback)
        include_untracked: Include untracked files in checkpoint
        dry_run: Preview what would happen without making changes

    Returns:
        Dict with checkpoint details
    """
    project = Path(project_path).resolve()

    if not _is_git_repo(str(project)):
        return {
            "success": False,
            "error": "Not a git repository. Initialize with 'git init' first."
        }

    if action == "create":
        return await _create_checkpoint(
            str(project), message, include_untracked, dry_run
        )
    elif action == "list":
        return await _list_checkpoints(str(project))
    elif action == "rollback":
        return await _rollback_checkpoint(
            str(project), checkpoint_id, dry_run
        )
    else:
        return {
            "success": False,
            "error": f"Unknown action: {action}. Use 'create', 'list', or 'rollback'."
        }


async def _create_checkpoint(
    project_path: str,
    message: Optional[str],
    include_untracked: bool,
    dry_run: bool
) -> Dict[str, Any]:
    """Create a new checkpoint."""
    if not message:
        return {
            "success": False,
            "error": "Message required for checkpoint. Describe what you did."
        }

    # Check for changes
    status = _run_git(project_path, ["status", "--porcelain"])
    if not status.stdout.strip():
        return {
            "success": False,
            "error": "No changes to checkpoint."
        }

    # Parse changes
    changes = []
    for line in status.stdout.strip().split("\n"):
        if line:
            status_code = line[:2].strip()
            file_path = line[3:]
            changes.append({"status": status_code, "file": file_path})

    if dry_run:
        return {
            "success": True,
            "dry_run": True,
            "would_commit": changes,
            "message": f"[CFA-SAFE] {message}"
        }

    # Stage changes
    if include_untracked:
        _run_git(project_path, ["add", "-A"])
    else:
        _run_git(project_path, ["add", "-u"])

    # Create commit
    commit_message = f"[CFA-SAFE] {message}"
    result = _run_git(project_path, ["commit", "-m", commit_message], check=False)

    if result.returncode != 0:
        return {
            "success": False,
            "error": f"Failed to create checkpoint: {result.stderr}"
        }

    # Get commit hash
    hash_result = _run_git(project_path, ["rev-parse", "HEAD"])
    commit_hash = hash_result.stdout.strip()[:8]

    return {
        "success": True,
        "action": "created",
        "checkpoint_id": commit_hash,
        "message": message,
        "files_committed": len(changes),
        "changes": changes[:10],  # Show first 10
        "rollback_command": f"cfa.checkpoint(action='rollback', checkpoint_id='{commit_hash}')"
    }


async def _list_checkpoints(project_path: str) -> Dict[str, Any]:
    """List all CFA checkpoints."""
    # Get commits with [CFA-SAFE] prefix
    result = _run_git(
        project_path,
        ["log", "--oneline", "--grep=[CFA-SAFE]", "-n", "20"],
        check=False
    )

    if result.returncode != 0 or not result.stdout.strip():
        return {
            "success": True,
            "count": 0,
            "checkpoints": [],
            "message": "No CFA checkpoints found."
        }

    checkpoints = []
    for line in result.stdout.strip().split("\n"):
        if line:
            parts = line.split(" ", 1)
            commit_hash = parts[0]
            message = parts[1].replace("[CFA-SAFE] ", "") if len(parts) > 1 else ""
            checkpoints.append({
                "id": commit_hash,
                "message": message
            })

    return {
        "success": True,
        "count": len(checkpoints),
        "checkpoints": checkpoints
    }


async def _rollback_checkpoint(
    project_path: str,
    checkpoint_id: Optional[str],
    dry_run: bool
) -> Dict[str, Any]:
    """Rollback to a checkpoint."""
    if not checkpoint_id:
        # Default to most recent checkpoint
        list_result = await _list_checkpoints(project_path)
        if list_result["count"] == 0:
            return {
                "success": False,
                "error": "No checkpoints to rollback to."
            }
        checkpoint_id = list_result["checkpoints"][0]["id"]

    # Verify checkpoint exists
    verify = _run_git(
        project_path,
        ["cat-file", "-t", checkpoint_id],
        check=False
    )
    if verify.returncode != 0:
        return {
            "success": False,
            "error": f"Checkpoint '{checkpoint_id}' not found."
        }

    # Show what would change
    diff_result = _run_git(
        project_path,
        ["diff", "--stat", f"{checkpoint_id}..HEAD"],
        check=False
    )

    if dry_run:
        return {
            "success": True,
            "dry_run": True,
            "checkpoint_id": checkpoint_id,
            "would_revert": diff_result.stdout.strip() if diff_result.stdout else "No changes"
        }

    # Check for uncommitted changes
    status = _run_git(project_path, ["status", "--porcelain"])
    if status.stdout.strip():
        return {
            "success": False,
            "error": "Uncommitted changes detected. Create a checkpoint first or stash changes."
        }

    # Perform rollback
    result = _run_git(
        project_path,
        ["reset", "--hard", checkpoint_id],
        check=False
    )

    if result.returncode != 0:
        return {
            "success": False,
            "error": f"Rollback failed: {result.stderr}"
        }

    return {
        "success": True,
        "action": "rolled_back",
        "checkpoint_id": checkpoint_id,
        "message": "Successfully rolled back. Your code is now at this checkpoint."
    }
