"""
MCP Tool: file.insert_at_line

Insert content at a specific line.
"""

from typing import Any, Dict
from pathlib import Path

from src.core.project import get_project_paths


async def file_lines_insert(
    project_path: str,
    file_path: str,
    line: int,
    content: str,
    insert_after: bool = False
) -> Dict[str, Any]:
    """
    Insert content at a specific line number.

    Inserts new content before or after a specified line,
    shifting existing content as needed.

    Args:
        project_path: Path to the project root
        file_path: Relative path to the file
        line: Line number for insertion (1-indexed)
        content: Content to insert
        insert_after: Insert after the line instead of before (default: False)

    Returns:
        Dictionary with:
            - success: Boolean
            - file_path: Modified file path
            - inserted_at: Line number where content starts
            - lines_inserted: Number of lines inserted
            - new_line_count: Total lines after insertion
            - message: Human-readable status

    Example:
        # Insert import at beginning of file
        result = await file_lines_insert(
            project_path="/projects/my-app",
            file_path="src/main.py",
            line=1,
            content="import logging\\n"
        )

        # Insert after specific line
        result = await file_lines_insert(
            project_path="/projects/my-app",
            file_path="src/models.py",
            line=25,
            content="    # New field added\\n    status: str = 'active'",
            insert_after=True
        )

        # Insert multi-line content
        result = await file_lines_insert(
            project_path="/projects/my-app",
            file_path="src/utils.py",
            line=50,
            content='''
def helper_function():
    \"\"\"A new helper function.\"\"\"
    return True
'''
        )

        # Insert at end of file (use line > total_lines)
        result = await file_lines_insert(
            project_path="/projects/my-app",
            file_path="src/app.py",
            line=999999,  # Will insert at end
            content="\\n# End of file"
        )

    Notes:
        - Line numbers are 1-indexed
        - If line > total lines, inserts at end of file
        - Content automatically gets proper line endings
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
        file_content = full_path.read_text(encoding="utf-8")
        lines = file_content.splitlines(keepends=True)
        total_lines = len(lines)

        # Validate line number
        if line < 1:
            return {
                "success": False,
                "error": f"Line number must be >= 1, got {line}"
            }

        # Prepare content to insert
        insert_lines = content.splitlines(keepends=True)
        if insert_lines and not insert_lines[-1].endswith("\n"):
            insert_lines[-1] += "\n"

        # Calculate insertion point
        if line > total_lines:
            # Insert at end
            insert_idx = total_lines
            actual_line = total_lines + 1
        elif insert_after:
            insert_idx = line  # After line N means index N
            actual_line = line + 1
        else:
            insert_idx = line - 1  # Before line N means index N-1
            actual_line = line

        # Insert content
        new_lines = lines[:insert_idx] + insert_lines + lines[insert_idx:]

        # Write new content
        new_content = "".join(new_lines)
        full_path.write_text(new_content, encoding="utf-8")

        return {
            "success": True,
            "file_path": str(full_path),
            "inserted_at": actual_line,
            "lines_inserted": len(insert_lines),
            "original_line_count": total_lines,
            "new_line_count": len(new_lines),
            "message": f"Inserted {len(insert_lines)} line(s) at line {actual_line}"
        }

    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to insert content: {str(e)}"
        }
