"""
MCP Tool: file.delete_lines

Delete specific lines from a file.
"""

from typing import Any, Dict, List, Union
from pathlib import Path

from src.core.project import get_project_paths


async def file_lines_delete(
    project_path: str,
    file_path: str,
    lines: Union[int, List[int], str]
) -> Dict[str, Any]:
    """
    Delete specific lines from a file.

    Removes one or more lines from a file by line number.
    Supports single lines, lists, and ranges.

    Args:
        project_path: Path to the project root
        file_path: Relative path to the file
        lines: Lines to delete. Can be:
               - Single line number: 10
               - List of line numbers: [5, 10, 15]
               - Range string: "10-20" (inclusive)
               - Multiple ranges: "5-10,15-20"

    Returns:
        Dictionary with:
            - success: Boolean
            - file_path: Modified file path
            - lines_deleted: Number of lines removed
            - deleted_content: Content of deleted lines
            - new_line_count: Total lines after deletion
            - message: Human-readable status

    Example:
        # Delete a single line
        result = await file_lines_delete(
            project_path="/projects/my-app",
            file_path="src/config.py",
            lines=42
        )

        # Delete multiple specific lines
        result = await file_lines_delete(
            project_path="/projects/my-app",
            file_path="src/routes.py",
            lines=[5, 10, 15, 20]
        )

        # Delete a range of lines
        result = await file_lines_delete(
            project_path="/projects/my-app",
            file_path="src/legacy.py",
            lines="100-150"
        )

        # Delete multiple ranges
        result = await file_lines_delete(
            project_path="/projects/my-app",
            file_path="src/cleanup.py",
            lines="10-20,50-60"
        )

    Notes:
        - Line numbers are 1-indexed
        - Invalid line numbers are silently ignored
        - Returns deleted content for review/undo
    """
    try:
        paths = get_project_paths(project_path)
        base_path = paths["root"]
        full_path = base_path / file_path

        if not full_path.exists():
            return {
                "success": False,
                "error": f"File not found: {file_path}"
            }

        # Read file
        content = full_path.read_text(encoding="utf-8")
        original_lines = content.splitlines(keepends=True)
        total_lines = len(original_lines)

        # Parse line numbers to delete
        lines_to_delete = set()

        if isinstance(lines, int):
            lines_to_delete.add(lines)
        elif isinstance(lines, list):
            lines_to_delete.update(lines)
        elif isinstance(lines, str):
            # Parse range string like "10-20" or "5-10,15-20"
            for part in lines.split(","):
                part = part.strip()
                if "-" in part:
                    try:
                        start, end = part.split("-", 1)
                        start = int(start.strip())
                        end = int(end.strip())
                        lines_to_delete.update(range(start, end + 1))
                    except ValueError:
                        return {
                            "success": False,
                            "error": f"Invalid range format: {part}"
                        }
                else:
                    try:
                        lines_to_delete.add(int(part))
                    except ValueError:
                        return {
                            "success": False,
                            "error": f"Invalid line number: {part}"
                        }

        # Filter to valid line numbers
        valid_lines = {ln for ln in lines_to_delete if 1 <= ln <= total_lines}

        if not valid_lines:
            return {
                "success": True,
                "file_path": str(full_path),
                "lines_deleted": 0,
                "message": "No valid line numbers to delete"
            }

        # Collect deleted content and filter lines
        deleted_content = []
        new_lines = []

        for i, line in enumerate(original_lines, 1):
            if i in valid_lines:
                deleted_content.append(f"{i}: {line.rstrip()}")
            else:
                new_lines.append(line)

        # Write new content
        new_content = "".join(new_lines)
        full_path.write_text(new_content, encoding="utf-8")

        return {
            "success": True,
            "file_path": str(full_path),
            "lines_deleted": len(valid_lines),
            "deleted_content": "\n".join(deleted_content),
            "original_line_count": total_lines,
            "new_line_count": len(new_lines),
            "message": f"Deleted {len(valid_lines)} line(s) from {file_path}"
        }

    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to delete lines: {str(e)}"
        }
