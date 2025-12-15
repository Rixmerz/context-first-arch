"""
MCP Tool: file.list

List directory contents with filtering options.
"""

from typing import Any, Dict, List, Optional
from pathlib import Path
import fnmatch

from src.core.project import get_project_paths


async def file_list(
    project_path: str,
    directory: str = ".",
    recursive: bool = False,
    pattern: Optional[str] = None,
    include_hidden: bool = False,
    max_depth: int = -1,
    file_types: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    List directory contents with filtering options.

    Provides comprehensive directory listing with support for
    recursion, glob patterns, and file type filtering.

    Args:
        project_path: Path to the project root
        directory: Relative path to list (default: "." for project root)
        recursive: Whether to list subdirectories recursively
        pattern: Glob pattern to filter (e.g., "*.py", "test_*")
        include_hidden: Include hidden files/directories (default: False)
        max_depth: Maximum recursion depth (-1 for unlimited)
        file_types: Filter by extensions (e.g., [".py", ".ts"])

    Returns:
        Dictionary with:
            - success: Boolean
            - directory: Listed directory path
            - entries: List of entries with:
                - name: File/directory name
                - path: Relative path from project
                - type: "file" or "directory"
                - size: Size in bytes (files only)
                - extension: File extension (if any)
            - total_files: Number of files found
            - total_directories: Number of directories found
            - truncated: Whether results were truncated

    Example:
        # List project root
        result = await file_list(
            project_path="/projects/my-app",
            directory="."
        )

        # List all Python files recursively
        result = await file_list(
            project_path="/projects/my-app",
            directory="src",
            recursive=True,
            pattern="*.py"
        )

        # List TypeScript and JavaScript files
        result = await file_list(
            project_path="/projects/my-app",
            directory="src",
            recursive=True,
            file_types=[".ts", ".tsx", ".js", ".jsx"]
        )

        # List with depth limit
        result = await file_list(
            project_path="/projects/my-app",
            directory=".",
            recursive=True,
            max_depth=2
        )
    """
    try:
        paths = get_project_paths(project_path)
        base_path = paths["root"]
        target_dir = base_path / directory

        if not target_dir.exists():
            return {
                "success": False,
                "error": f"Directory not found: {directory}"
            }

        if not target_dir.is_dir():
            return {
                "success": False,
                "error": f"Not a directory: {directory}"
            }

        entries = []
        total_files = 0
        total_dirs = 0
        max_entries = 1000  # Limit to prevent overwhelming output

        def should_include(path: Path, current_depth: int) -> bool:
            """Check if path should be included based on filters."""
            name = path.name

            # Hidden file check
            if not include_hidden and name.startswith("."):
                return False

            # Depth check
            if max_depth >= 0 and current_depth > max_depth:
                return False

            return True

        def matches_filters(path: Path) -> bool:
            """Check if file matches pattern and type filters."""
            name = path.name

            # Pattern filter
            if pattern and not fnmatch.fnmatch(name, pattern):
                return False

            # File type filter
            if file_types and path.is_file():
                ext = path.suffix.lower()
                if ext not in [t.lower() for t in file_types]:
                    return False

            return True

        def list_directory(dir_path: Path, depth: int = 0):
            nonlocal total_files, total_dirs

            if len(entries) >= max_entries:
                return

            try:
                items = sorted(dir_path.iterdir(), key=lambda p: (p.is_file(), p.name.lower()))
            except PermissionError:
                return

            for item in items:
                if not should_include(item, depth):
                    continue

                if item.is_dir():
                    total_dirs += 1
                    if matches_filters(item) or recursive:
                        rel_path = str(item.relative_to(base_path))
                        entries.append({
                            "name": item.name,
                            "path": rel_path,
                            "type": "directory"
                        })

                    if recursive and (max_depth < 0 or depth < max_depth):
                        list_directory(item, depth + 1)

                elif item.is_file():
                    if matches_filters(item):
                        total_files += 1
                        rel_path = str(item.relative_to(base_path))
                        entries.append({
                            "name": item.name,
                            "path": rel_path,
                            "type": "file",
                            "size": item.stat().st_size,
                            "extension": item.suffix if item.suffix else None
                        })

        list_directory(target_dir)

        return {
            "success": True,
            "directory": str(target_dir.relative_to(base_path)) if target_dir != base_path else ".",
            "entries": entries[:max_entries],
            "total_files": total_files,
            "total_directories": total_dirs,
            "truncated": len(entries) >= max_entries
        }

    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to list directory: {str(e)}"
        }
