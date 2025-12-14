"""
MCP Tool: map.auto_update

Auto-update map.md when implementation or contract files change.
"""

from typing import Any, Dict, List
from pathlib import Path
import subprocess

from src.core.map_generator import update_map_file
from src.core.project import get_project_paths


async def map_auto_update(
    project_path: str,
    force: bool = False
) -> Dict[str, Any]:
    """
    Auto-update map.md if implementation or contract files have changed.

    Detects changes using git (if available) or file modification times.
    Regenerates map.md only if relevant files have changed since last update.

    Args:
        project_path: Path to CFA project
        force: Force update even if no changes detected

    Returns:
        Dictionary with:
            - success: Boolean
            - updated: Whether map was updated
            - changes_detected: List of changed files
            - map_file: Path to map.md
            - method: Detection method used (git/mtime)

    Example:
        # Auto-update if changes detected
        result = await map_auto_update(
            project_path="/projects/my-app"
        )

        # Force update
        result = await map_auto_update(
            project_path="/projects/my-app",
            force=True
        )
    """
    try:
        path = Path(project_path)

        # Validate CFA project
        if not (path / ".claude").exists():
            return {"success": False, "error": "Not a CFA project (missing .claude/)"}

        map_file = path / ".claude" / "map.md"

        if not map_file.exists():
            return {
                "success": False,
                "error": "map.md not found in .claude/",
                "hint": "Initialize project with project.init first"
            }

        # Get map.md last modification time
        map_mtime = map_file.stat().st_mtime

        # Detect changes
        changes_detected, method = _detect_changes(path, map_mtime)

        if not changes_detected and not force:
            return {
                "success": True,
                "updated": False,
                "changes_detected": [],
                "map_file": str(map_file.relative_to(path)),
                "method": method,
                "message": "✓ No changes detected, map.md is up to date"
            }

        # Update map
        try:
            # Call the map_generator update_map_file function
            stats = update_map_file(str(path))

            return {
                "success": True,
                "updated": True,
                "changes_detected": changes_detected,
                "map_file": str(map_file.relative_to(path)),
                "method": method,
                "stats": stats,
                "message": _format_message(force, len(changes_detected), method)
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to update map: {str(e)}"
            }

    except Exception as e:
        return {
            "success": False,
            "error": f"Map auto-update failed: {str(e)}"
        }


def _detect_changes(project_path: Path, map_mtime: float) -> tuple:
    """
    Detect changes in implementation and contract files.

    Returns:
        Tuple of (changed_files, method)
    """
    # Try git first
    git_changes = _get_git_changes(project_path, map_mtime)
    if git_changes is not None:
        return git_changes, "git"

    # Fallback to mtime
    mtime_changes = _get_mtime_changes(project_path, map_mtime)
    return mtime_changes, "mtime"


def _get_git_changes(project_path: Path, since_time: float) -> List[str]:
    """Get changed files using git."""
    try:
        # Check if git repo exists
        git_dir = project_path / ".git"
        if not git_dir.exists():
            return None

        # Get modified files since timestamp
        import datetime
        since_date = datetime.datetime.fromtimestamp(since_time).isoformat()

        result = subprocess.run(
            ["git", "log", "--since", since_date, "--name-only", "--pretty=format:", "--", "impl/", "contracts/"],
            cwd=str(project_path),
            capture_output=True,
            text=True,
            timeout=5
        )

        if result.returncode != 0:
            return None

        # Parse changed files
        changed_files = []
        for line in result.stdout.split("\n"):
            line = line.strip()
            if line and (line.startswith("impl/") or line.startswith("contracts/")):
                changed_files.append(line)

        return list(set(changed_files))  # Remove duplicates

    except Exception:
        return None


def _get_mtime_changes(project_path: Path, map_mtime: float) -> List[str]:
    """Get changed files using modification time."""
    changed_files = []

    # Get project paths (handles both v1 and v2)
    paths = get_project_paths(project_path)

    # Check impl directory
    impl_dir = paths["impl_dir"]
    if impl_dir.exists():
        for file_path in impl_dir.rglob("*"):
            if file_path.is_file() and file_path.stat().st_mtime > map_mtime:
                changed_files.append(str(file_path.relative_to(project_path)))

    # Check contracts directory
    contracts_dir = paths["contracts_dir"]
    if contracts_dir.exists():
        for file_path in contracts_dir.rglob("*.contract.md"):
            if file_path.stat().st_mtime > map_mtime:
                changed_files.append(str(file_path.relative_to(project_path)))

    return changed_files


def _format_message(force: bool, change_count: int, method: str) -> str:
    """Generate human-readable message."""
    if force:
        return f"✓ Force updated map.md (detection: {method})"

    return f"✓ Updated map.md: {change_count} file(s) changed (detection: {method})"
