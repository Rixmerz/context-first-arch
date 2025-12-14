"""
MCP Tool: file.replace_lines

Replace specific lines in a file.
"""

from typing import Any, Dict, List
from pathlib import Path

from src.core.project import get_project_paths


async def file_lines_replace(
    project_path: str,
    file_path: str,
    start_line: int,
    end_line: int,
    new_content: str
) -> Dict[str, Any]:
    """
    Replace a range of lines with new content.

    Replaces lines from start_line to end_line (inclusive)
    with the provided new content.

    Args:
        project_path: Path to the project root
        file_path: Relative path to the file
        start_line: First line to replace (1-indexed)
        end_line: Last line to replace (1-indexed, inclusive)
        new_content: New content to insert

    Returns:
        Dictionary with:
            - success: Boolean
            - file_path: Modified file path
            - lines_replaced: Number of original lines replaced
            - lines_inserted: Number of new lines inserted
            - replaced_content: Original content that was replaced
            - message: Human-readable status

    Example:
        # Replace a single line
        result = await file_lines_replace(
            project_path="/projects/my-app",
            file_path="src/config.py",
            start_line=10,
            end_line=10,
            new_content="DEBUG = False"
        )

        # Replace a function (lines 20-35) with new implementation
        result = await file_lines_replace(
            project_path="/projects/my-app",
            file_path="src/utils.py",
            start_line=20,
            end_line=35,
            new_content='''def calculate_total(items):
    \"\"\"Calculate total with tax.\"\"\"
    subtotal = sum(item.price for item in items)
    tax = subtotal * 0.1
    return subtotal + tax'''
        )

        # Replace block of imports
        result = await file_lines_replace(
            project_path="/projects/my-app",
            file_path="src/main.py",
            start_line=1,
            end_line=5,
            new_content='''from typing import Optional, List
from dataclasses import dataclass
from pathlib import Path'''
        )

    Notes:
        - Line numbers are 1-indexed
        - Both start_line and end_line are inclusive
        - Returns replaced content for review/undo
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
        lines = content.splitlines(keepends=True)
        total_lines = len(lines)

        # Validate line numbers
        if start_line < 1:
            return {
                "success": False,
                "error": f"start_line must be >= 1, got {start_line}"
            }

        if end_line < start_line:
            return {
                "success": False,
                "error": f"end_line ({end_line}) must be >= start_line ({start_line})"
            }

        if start_line > total_lines:
            return {
                "success": False,
                "error": f"start_line ({start_line}) exceeds file length ({total_lines})"
            }

        # Adjust end_line if beyond file
        end_line = min(end_line, total_lines)

        # Extract replaced content
        replaced_lines = lines[start_line - 1:end_line]
        replaced_content = "".join(replaced_lines)

        # Prepare new content with proper line endings
        new_lines = new_content.splitlines(keepends=True)
        if new_lines and not new_lines[-1].endswith("\n"):
            new_lines[-1] += "\n"

        # Build new file content
        result_lines = (
            lines[:start_line - 1] +
            new_lines +
            lines[end_line:]
        )

        # Write new content
        new_file_content = "".join(result_lines)
        full_path.write_text(new_file_content, encoding="utf-8")

        lines_replaced = end_line - start_line + 1
        lines_inserted = len(new_lines)

        return {
            "success": True,
            "file_path": str(full_path),
            "lines_replaced": lines_replaced,
            "lines_inserted": lines_inserted,
            "line_range": f"{start_line}-{end_line}",
            "replaced_content": replaced_content.rstrip(),
            "message": f"Replaced {lines_replaced} line(s) with {lines_inserted} line(s)"
        }

    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to replace lines: {str(e)}"
        }
