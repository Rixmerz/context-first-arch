"""
Safe Points Module

Manages git-based safe points for rollback capability between AI interactions.
Extracted from prehook_commit.py as part of CFA migration.
"""

from typing import Any, Dict, List, Optional
from datetime import datetime
from pathlib import Path
import subprocess
import uuid

from .models import SafePoint
from .storage import OrchestrationStorage


# Default commit message prefix
DEFAULT_PREFIX = "[Nova]"


class SafePointManager:
    """Manages git-based safe points for rollback capability."""

    def __init__(self, storage: OrchestrationStorage):
        """
        Initialize manager with storage.

        Args:
            storage: OrchestrationStorage instance for persistence
        """
        self.storage = storage

    def create(
        self,
        project_path: str,
        task_summary: str,
        files_changed: Optional[List[str]] = None,
        prefix: str = DEFAULT_PREFIX,
        include_untracked: bool = True,
        dry_run: bool = False
    ) -> Dict[str, Any]:
        """
        Create a safe point by committing current changes.

        Creates an automatic git commit after successful AI interactions,
        providing a safe restoration point.

        Args:
            project_path: Path to the project root (must be a git repo)
            task_summary: Brief description of what was done
            files_changed: Optional list of specific files to commit
            prefix: Commit message prefix (default "[Nova]")
            include_untracked: Include untracked files in commit
            dry_run: Preview what would be committed without committing

        Returns:
            Dictionary with:
                - success: Operation success
                - safe_point_id: Unique identifier
                - commit_hash: Git commit hash
                - files_committed: List of files in commit
        """
        try:
            project = Path(project_path)

            # Verify it's a git repository
            git_dir = project / ".git"
            if not git_dir.exists():
                return {
                    "success": False,
                    "error": f"Not a git repository: {project_path}",
                    "hint": "Initialize git with 'git init' first"
                }

            # Get current git status
            status_result = self._get_git_status(project_path)

            if not status_result["success"]:
                return status_result

            # Check if there are changes to commit
            has_changes = (
                status_result["staged"] or
                status_result["unstaged"] or
                (include_untracked and status_result["untracked"])
            )

            if not has_changes:
                return {
                    "success": True,
                    "no_changes": True,
                    "message": "No changes to commit - workspace is clean",
                    "git_status": status_result
                }

            # Format commit message
            message = self._format_commit_message(task_summary, prefix)

            # Determine files to stage
            files_to_stage = files_changed or []
            if not files_to_stage:
                # Stage all changes
                if include_untracked:
                    files_to_stage = (
                        status_result["staged"] +
                        status_result["unstaged"] +
                        status_result["untracked"]
                    )
                else:
                    files_to_stage = status_result["staged"] + status_result["unstaged"]

            if dry_run:
                return {
                    "success": True,
                    "dry_run": True,
                    "would_commit": {
                        "message": message,
                        "files": files_to_stage,
                        "file_count": len(files_to_stage)
                    },
                    "message": f"Would commit {len(files_to_stage)} files with message: {message}"
                }

            # Stage and commit
            commit_result = self._create_commit(project_path, message, files_to_stage)

            if not commit_result["success"]:
                return commit_result

            # Create safe point record
            safe_point_id = str(uuid.uuid4())
            safe_point = SafePoint(
                id=safe_point_id,
                commit_hash=commit_result["commit_hash"],
                message=task_summary,
                timestamp=datetime.now(),
                files_changed=files_to_stage,
                project_path=project_path
            )

            # Persist safe point
            self.storage.create_safe_point(safe_point)

            # Integrate with Memory Store
            self._store_in_memory(safe_point)

            return {
                "success": True,
                "safe_point_id": safe_point_id,
                "commit_hash": commit_result["commit_hash"],
                "commit_message": message,
                "files_committed": files_to_stage,
                "file_count": len(files_to_stage),
                "safe_point": self._serialize_safe_point(safe_point),
                "message": f"Safe point created: {commit_result['commit_hash'][:7]} - {task_summary}"
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to create safe point: {str(e)}"
            }

    def rollback(
        self,
        project_path: str,
        safe_point_id: Optional[str] = None,
        commit_hash: Optional[str] = None,
        mode: str = "preview"
    ) -> Dict[str, Any]:
        """
        Rollback to a previous safe point.

        Args:
            project_path: Path to the project root
            safe_point_id: ID of safe point to rollback to
            commit_hash: Alternative: specific commit hash to rollback to
            mode: "preview" to see what would change, "execute" to actually rollback

        Returns:
            Dictionary with rollback result
        """
        try:
            # Get target commit
            target_commit = None

            if safe_point_id:
                safe_point = self.storage.get_safe_point(safe_point_id)
                if not safe_point:
                    return {
                        "success": False,
                        "error": f"Safe point {safe_point_id} not found"
                    }
                target_commit = safe_point.commit_hash
            elif commit_hash:
                target_commit = commit_hash
            else:
                return {
                    "success": False,
                    "error": "Provide either safe_point_id or commit_hash"
                }

            # Get changes since target commit
            changes = self._get_changes_since(project_path, target_commit)

            if mode == "preview":
                return {
                    "success": True,
                    "preview": True,
                    "target_commit": target_commit,
                    "files_affected": changes.get("files", []),
                    "commits_to_revert": changes.get("commit_count", 0),
                    "message": f"Preview: Would rollback {changes.get('commit_count', 0)} commits affecting {len(changes.get('files', []))} files",
                    "warning": "Use mode='execute' to perform actual rollback"
                }

            # Execute rollback
            rollback_result = self._execute_rollback(project_path, target_commit)

            if not rollback_result["success"]:
                return rollback_result

            return {
                "success": True,
                "rolled_back_to": target_commit,
                "files_reverted": changes.get("files", []),
                "message": f"Rolled back to {target_commit[:7]}",
                "safe_point_id": safe_point_id
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Rollback failed: {str(e)}"
            }

    def list_safe_points(
        self,
        project_path: Optional[str] = None,
        limit: int = 10
    ) -> Dict[str, Any]:
        """
        List recent safe points.

        Args:
            project_path: Optional filter by project
            limit: Maximum safe points to return (default 10)

        Returns:
            Dictionary with safe points list
        """
        try:
            # Query safe points
            filters = {}
            if project_path:
                filters["project_path"] = project_path

            safe_points = self.storage.list_safe_points(
                project_path=project_path,
                limit=limit
            )

            # Serialize
            serialized = [self._serialize_safe_point(sp) for sp in safe_points]

            return {
                "success": True,
                "safe_points": serialized,
                "count": len(serialized)
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to list safe points: {str(e)}"
            }

    def _get_git_status(self, project_path: str) -> Dict[str, Any]:
        """
        Get current git status.

        Args:
            project_path: Path to git repository

        Returns:
            Dictionary with git status information
        """
        try:
            # Get staged files
            staged = subprocess.run(
                ["git", "diff", "--cached", "--name-only"],
                cwd=project_path,
                capture_output=True,
                text=True
            )

            # Get unstaged files
            unstaged = subprocess.run(
                ["git", "diff", "--name-only"],
                cwd=project_path,
                capture_output=True,
                text=True
            )

            # Get untracked files
            untracked = subprocess.run(
                ["git", "ls-files", "--others", "--exclude-standard"],
                cwd=project_path,
                capture_output=True,
                text=True
            )

            # Get current branch
            branch = subprocess.run(
                ["git", "branch", "--show-current"],
                cwd=project_path,
                capture_output=True,
                text=True
            )

            return {
                "success": True,
                "clean": not (staged.stdout.strip() or unstaged.stdout.strip() or untracked.stdout.strip()),
                "staged": [f for f in staged.stdout.strip().split("\n") if f],
                "unstaged": [f for f in unstaged.stdout.strip().split("\n") if f],
                "untracked": [f for f in untracked.stdout.strip().split("\n") if f],
                "branch": branch.stdout.strip()
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Git status failed: {str(e)}"
            }

    def _create_commit(
        self,
        project_path: str,
        message: str,
        files: List[str]
    ) -> Dict[str, Any]:
        """
        Stage files and create commit.

        Args:
            project_path: Path to git repository
            message: Commit message
            files: Files to stage and commit

        Returns:
            Dictionary with commit result including commit hash
        """
        try:
            # Stage files
            for file in files:
                subprocess.run(
                    ["git", "add", file],
                    cwd=project_path,
                    check=True
                )

            # Create commit
            result = subprocess.run(
                ["git", "commit", "-m", message],
                cwd=project_path,
                capture_output=True,
                text=True
            )

            if result.returncode != 0:
                return {
                    "success": False,
                    "error": f"Commit failed: {result.stderr}"
                }

            # Get commit hash
            hash_result = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=project_path,
                capture_output=True,
                text=True
            )

            return {
                "success": True,
                "commit_hash": hash_result.stdout.strip()
            }

        except subprocess.CalledProcessError as e:
            return {
                "success": False,
                "error": f"Git operation failed: {str(e)}"
            }

    def _get_changes_since(
        self,
        project_path: str,
        commit_hash: str
    ) -> Dict[str, Any]:
        """
        Get changes since a specific commit.

        Args:
            project_path: Path to git repository
            commit_hash: Commit hash to compare from

        Returns:
            Dictionary with files changed and commit count
        """
        try:
            # Get files changed
            files_result = subprocess.run(
                ["git", "diff", "--name-only", f"{commit_hash}..HEAD"],
                cwd=project_path,
                capture_output=True,
                text=True
            )

            # Count commits
            count_result = subprocess.run(
                ["git", "rev-list", "--count", f"{commit_hash}..HEAD"],
                cwd=project_path,
                capture_output=True,
                text=True
            )

            return {
                "files": [f for f in files_result.stdout.strip().split("\n") if f],
                "commit_count": int(count_result.stdout.strip() or 0)
            }

        except Exception as e:
            return {"files": [], "commit_count": 0, "error": str(e)}

    def _execute_rollback(
        self,
        project_path: str,
        commit_hash: str
    ) -> Dict[str, Any]:
        """
        Execute rollback to specific commit.

        CAUTION: Uses git reset --hard which is destructive.

        Args:
            project_path: Path to git repository
            commit_hash: Commit hash to reset to

        Returns:
            Dictionary with rollback result
        """
        try:
            # Use git reset --hard (careful - destructive!)
            result = subprocess.run(
                ["git", "reset", "--hard", commit_hash],
                cwd=project_path,
                capture_output=True,
                text=True
            )

            if result.returncode != 0:
                return {
                    "success": False,
                    "error": f"Reset failed: {result.stderr}"
                }

            return {"success": True}

        except Exception as e:
            return {
                "success": False,
                "error": f"Rollback failed: {str(e)}"
            }

    def _format_commit_message(self, summary: str, prefix: str) -> str:
        """
        Format commit message with prefix and truncation.

        Args:
            summary: Task summary
            prefix: Message prefix

        Returns:
            Formatted commit message
        """
        max_length = 72

        # Truncate if needed
        if len(summary) > max_length - len(prefix) - 1:
            summary = summary[:max_length - len(prefix) - 4] + "..."

        return f"{prefix} {summary}"

    def _serialize_safe_point(self, safe_point: SafePoint) -> Dict[str, Any]:
        """
        Serialize safe point to dictionary for API responses.

        Args:
            safe_point: Safe point to serialize

        Returns:
            Dictionary representation
        """
        return {
            "id": safe_point.id,
            "commit_hash": safe_point.commit_hash,
            "message": safe_point.message,
            "timestamp": safe_point.timestamp.isoformat(),
            "files_changed": safe_point.files_changed,
            "project_path": safe_point.project_path
        }

    def _store_in_memory(self, safe_point: SafePoint):
        """
        Store safe point metadata in Memory Store for cross-session access.

        Args:
            safe_point: Safe point to store
        """
        try:
            from pathlib import Path as PathLib
            from src.features.memory import MemoryStore

            if safe_point.project_path:
                memory = MemoryStore(PathLib(safe_point.project_path))
                memory.set(
                    key=f"safe_point_{safe_point.id}",
                    value=f"Safe point created: {safe_point.message} (commit: {safe_point.commit_hash[:7]})",
                    tags=["nova", "safe_point", "git"]
                )
        except Exception:
            # Silently fail if Memory Store unavailable
            pass
