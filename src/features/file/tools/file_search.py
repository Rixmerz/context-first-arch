"""
MCP Tool: file.search

Search for patterns across files (enhanced grep).
"""

from typing import Any, Dict, List, Optional
from pathlib import Path
import re
import fnmatch

from src.core.project import get_project_paths


async def file_search(
    project_path: str,
    pattern: str,
    directory: str = ".",
    file_pattern: Optional[str] = None,
    use_regex: bool = False,
    case_sensitive: bool = True,
    context_lines: int = 0,
    max_results: int = 100,
    include_hidden: bool = False
) -> Dict[str, Any]:
    """
    Search for patterns across files (enhanced grep).

    Searches file contents for matching patterns with support for
    regex, context lines, and file filtering.

    Args:
        project_path: Path to the project root
        pattern: Search pattern (literal or regex)
        directory: Directory to search in (default: ".")
        file_pattern: Glob pattern for files (e.g., "*.py", "*.ts")
        use_regex: Use regex matching (default: False)
        case_sensitive: Case sensitive search (default: True)
        context_lines: Lines of context around matches (default: 0)
        max_results: Maximum number of matches (default: 100)
        include_hidden: Include hidden files (default: False)

    Returns:
        Dictionary with:
            - success: Boolean
            - pattern: Search pattern used
            - matches: List of matches with:
                - file: File path
                - line: Line number
                - column: Column of match
                - content: Line content
                - context_before: Lines before (if context_lines > 0)
                - context_after: Lines after (if context_lines > 0)
            - files_searched: Number of files searched
            - files_with_matches: Number of files with matches
            - total_matches: Total matches found
            - truncated: Whether results were truncated

    Example:
        # Simple text search
        result = await file_search(
            project_path="/projects/my-app",
            pattern="TODO"
        )

        # Search in Python files only
        result = await file_search(
            project_path="/projects/my-app",
            pattern="def process",
            file_pattern="*.py"
        )

        # Regex search with context
        result = await file_search(
            project_path="/projects/my-app",
            pattern="import.*from",
            use_regex=True,
            context_lines=2
        )

        # Case-insensitive search
        result = await file_search(
            project_path="/projects/my-app",
            pattern="error",
            case_sensitive=False
        )

    Notes:
        - Returns column position for precise location
        - Context lines show surrounding code
        - Respects .gitignore-like patterns for common ignores
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

        # Compile pattern
        flags = 0 if case_sensitive else re.IGNORECASE
        if use_regex:
            try:
                regex = re.compile(pattern, flags)
            except re.error as e:
                return {
                    "success": False,
                    "error": f"Invalid regex: {str(e)}"
                }
        else:
            regex = re.compile(re.escape(pattern), flags)

        # Common directories to ignore
        ignore_dirs = {
            ".git", ".svn", ".hg", "node_modules", "__pycache__",
            ".venv", "venv", ".env", "dist", "build", ".next",
            "target", ".idea", ".vscode"
        }

        matches = []
        files_searched = 0
        files_with_matches = set()

        def should_search_file(file_path: Path) -> bool:
            """Check if file should be searched."""
            # Skip hidden files unless requested
            if not include_hidden:
                if any(part.startswith(".") for part in file_path.parts):
                    return False

            # Skip ignored directories
            for part in file_path.parts:
                if part in ignore_dirs:
                    return False

            # Check file pattern
            if file_pattern and not fnmatch.fnmatch(file_path.name, file_pattern):
                return False

            # Skip binary files (simple heuristic)
            binary_extensions = {
                ".pyc", ".pyo", ".so", ".o", ".a", ".lib", ".dll",
                ".exe", ".bin", ".png", ".jpg", ".jpeg", ".gif",
                ".ico", ".pdf", ".zip", ".tar", ".gz", ".woff",
                ".woff2", ".ttf", ".eot"
            }
            if file_path.suffix.lower() in binary_extensions:
                return False

            return True

        for file_path in search_dir.rglob("*"):
            if len(matches) >= max_results:
                break

            if not file_path.is_file():
                continue

            if not should_search_file(file_path):
                continue

            files_searched += 1

            try:
                content = file_path.read_text(encoding="utf-8", errors="ignore")
                lines = content.splitlines()

                for line_num, line in enumerate(lines, 1):
                    if len(matches) >= max_results:
                        break

                    for match in regex.finditer(line):
                        rel_path = str(file_path.relative_to(base_path))
                        files_with_matches.add(rel_path)

                        result_entry = {
                            "file": rel_path,
                            "line": line_num,
                            "column": match.start() + 1,
                            "content": line.rstrip(),
                            "match": match.group()
                        }

                        # Add context if requested
                        if context_lines > 0:
                            start_ctx = max(0, line_num - 1 - context_lines)
                            end_ctx = min(len(lines), line_num + context_lines)

                            result_entry["context_before"] = [
                                f"{i+1}: {lines[i]}"
                                for i in range(start_ctx, line_num - 1)
                            ]
                            result_entry["context_after"] = [
                                f"{i+1}: {lines[i]}"
                                for i in range(line_num, end_ctx)
                            ]

                        matches.append(result_entry)

                        if len(matches) >= max_results:
                            break

            except (UnicodeDecodeError, PermissionError):
                continue

        return {
            "success": True,
            "pattern": pattern,
            "pattern_type": "regex" if use_regex else "literal",
            "search_directory": directory,
            "matches": matches,
            "files_searched": files_searched,
            "files_with_matches": len(files_with_matches),
            "total_matches": len(matches),
            "truncated": len(matches) >= max_results
        }

    except Exception as e:
        return {
            "success": False,
            "error": f"Search failed: {str(e)}"
        }
