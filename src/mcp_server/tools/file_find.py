"""
MCP Tool: file.find

Find files matching a pattern.
"""

from typing import Any, Dict, List, Optional
from pathlib import Path
import fnmatch
import re

from src.core.project import get_project_paths


async def file_find(
    project_path: str,
    pattern: str,
    directory: str = ".",
    use_regex: bool = False,
    include_hidden: bool = False,
    max_results: int = 100
) -> Dict[str, Any]:
    """
    Find files matching a pattern.

    Searches for files using glob patterns or regular expressions.
    Supports flexible matching across the project.

    Args:
        project_path: Path to the project root
        pattern: Search pattern (glob or regex)
                 Glob examples: "*.py", "test_*.ts", "**/*.json"
                 Regex examples: ".*\\.py$", "test_\\d+\\.js"
        directory: Starting directory for search (default: ".")
        use_regex: Use regex instead of glob pattern (default: False)
        include_hidden: Include hidden files (default: False)
        max_results: Maximum number of results (default: 100)

    Returns:
        Dictionary with:
            - success: Boolean
            - pattern: Search pattern used
            - matches: List of matching files with:
                - path: Relative path from project
                - name: File name
                - size: File size in bytes
                - directory: Parent directory
            - count: Number of matches found
            - truncated: Whether results were truncated

    Example:
        # Find all Python files
        result = await file_find(
            project_path="/projects/my-app",
            pattern="*.py"
        )

        # Find all test files
        result = await file_find(
            project_path="/projects/my-app",
            pattern="test_*.py"
        )

        # Find files with regex
        result = await file_find(
            project_path="/projects/my-app",
            pattern=".*_handler\\.py$",
            use_regex=True
        )

        # Find in specific directory
        result = await file_find(
            project_path="/projects/my-app",
            pattern="*.ts",
            directory="src/components"
        )
    """
    try:
        paths = get_project_paths(project_path)
        base_path = paths["root"]
        search_dir = base_path / directory

        if not search_dir.exists():
            return {
                "success": False,
                "error": f"Directory not found: {directory}"
            }

        matches = []

        # Compile regex if needed
        if use_regex:
            try:
                regex = re.compile(pattern)
            except re.error as e:
                return {
                    "success": False,
                    "error": f"Invalid regex pattern: {str(e)}"
                }

        def matches_pattern(name: str) -> bool:
            if use_regex:
                return bool(regex.search(name))
            else:
                return fnmatch.fnmatch(name, pattern)

        # Search for files
        for file_path in search_dir.rglob("*"):
            if len(matches) >= max_results:
                break

            if not file_path.is_file():
                continue

            # Skip hidden files unless requested
            if not include_hidden:
                if any(part.startswith(".") for part in file_path.parts):
                    continue

            # Check pattern match
            if matches_pattern(file_path.name):
                rel_path = str(file_path.relative_to(base_path))
                matches.append({
                    "path": rel_path,
                    "name": file_path.name,
                    "size": file_path.stat().st_size,
                    "directory": str(file_path.parent.relative_to(base_path))
                })

        # Sort by path
        matches.sort(key=lambda m: m["path"])

        return {
            "success": True,
            "pattern": pattern,
            "pattern_type": "regex" if use_regex else "glob",
            "search_directory": directory,
            "matches": matches,
            "count": len(matches),
            "truncated": len(matches) >= max_results
        }

    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to find files: {str(e)}"
        }
