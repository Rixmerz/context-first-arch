"""
MCP Tool: file.read

Read file contents with optional line range.
"""

from typing import Any, Dict, Optional
from pathlib import Path

from src.core.project import get_project_paths


async def file_read(
    project_path: str,
    file_path: str,
    start_line: Optional[int] = None,
    end_line: Optional[int] = None,
    include_line_numbers: bool = True
) -> Dict[str, Any]:
    """
    Read file contents with optional line range.

    Provides flexible file reading with line range support,
    respecting CFA project structure.

    Args:
        project_path: Path to the project root
        file_path: Relative path to the file
        start_line: Optional starting line (1-indexed, inclusive)
        end_line: Optional ending line (1-indexed, inclusive)
        include_line_numbers: Whether to prefix lines with numbers (default: True)

    Returns:
        Dictionary with:
            - success: Boolean
            - file_path: Full path to the file
            - content: File content (with optional line numbers)
            - total_lines: Total number of lines in file
            - lines_read: Number of lines returned
            - range: Line range read (if specified)
            - encoding: File encoding detected

    Example:
        # Read entire file
        result = await file_read(
            project_path="/projects/my-app",
            file_path="src/services/auth.py"
        )

        # Read specific line range
        result = await file_read(
            project_path="/projects/my-app",
            file_path="src/models/user.py",
            start_line=10,
            end_line=50
        )

        # Read without line numbers
        result = await file_read(
            project_path="/projects/my-app",
            file_path="config.json",
            include_line_numbers=False
        )
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

        if not full_path.is_file():
            return {
                "success": False,
                "error": f"Not a file: {file_path}"
            }

        # Read file content
        try:
            content = full_path.read_text(encoding="utf-8")
            encoding = "utf-8"
        except UnicodeDecodeError:
            content = full_path.read_text(encoding="latin-1")
            encoding = "latin-1"

        lines = content.splitlines(keepends=True)
        total_lines = len(lines)

        # Apply line range if specified
        if start_line is not None or end_line is not None:
            start_idx = (start_line - 1) if start_line else 0
            end_idx = end_line if end_line else total_lines

            # Validate range
            start_idx = max(0, start_idx)
            end_idx = min(total_lines, end_idx)

            lines = lines[start_idx:end_idx]
            line_offset = start_idx + 1
        else:
            line_offset = 1

        # Format output
        if include_line_numbers:
            formatted_lines = []
            for i, line in enumerate(lines):
                line_num = line_offset + i
                formatted_lines.append(f"{line_num:4d}→{line.rstrip()}")
            output = "\n".join(formatted_lines)
        else:
            output = "".join(lines)

        return {
            "success": True,
            "file_path": str(full_path),
            "content": output,
            "total_lines": total_lines,
            "lines_read": len(lines),
            "range": {
                "start": line_offset,
                "end": line_offset + len(lines) - 1
            } if (start_line or end_line) else None,
            "encoding": encoding
        }

    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to read file: {str(e)}"
        }
