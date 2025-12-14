"""
MCP Tool: file.edit_lines

Line-based file editing operations.
Consolidates: file.delete_lines + file.replace_lines + file.insert_at_line
"""

from typing import Any, Dict, List, Union, Literal, Optional
from pathlib import Path

from src.core.project import get_project_paths


async def file_edit_lines(
    project_path: str,
    file_path: str,
    operation: Literal["delete", "replace", "insert"],
    lines: Union[int, List[int], str, None] = None,
    content: Optional[str] = None,
    # For replace operation
    start_line: Optional[int] = None,
    end_line: Optional[int] = None,
    # For insert operation
    insert_after: bool = False
) -> Dict[str, Any]:
    """
    Line-based file editing. Use for text operations, symbol.replace for code.

    Unified tool for line-level file manipulation:
    - "delete": Remove lines by number, list, or range
    - "replace": Replace a range of lines with new content
    - "insert": Add content at a specific line

    Args:
        project_path: Path to the project root
        file_path: Relative path to the file
        operation: "delete", "replace", or "insert"
        lines: Line specification:
            - For delete: int, list[int], or range string "10-20"
            - For insert: single line number
            - For replace: use start_line/end_line instead
        content: Content for insert/replace operations
        start_line: First line to replace (for "replace" only)
        end_line: Last line to replace (for "replace" only)
        insert_after: Insert after line instead of before (for "insert" only)

    Returns:
        Dictionary with operation-specific results and:
            - success: Boolean
            - operation: The operation performed
            - file_path: Modified file path
            - message: Human-readable status

    Examples:
        # DELETE: Remove specific lines
        result = await file_edit_lines(
            project_path=".",
            file_path="src/config.py",
            operation="delete",
            lines="10-20"  # or [5, 10, 15] or 42
        )

        # REPLACE: Replace lines 20-35 with new content
        result = await file_edit_lines(
            project_path=".",
            file_path="src/utils.py",
            operation="replace",
            start_line=20,
            end_line=35,
            content="def new_function():\\n    pass"
        )

        # INSERT: Add content at line 1
        result = await file_edit_lines(
            project_path=".",
            file_path="src/main.py",
            operation="insert",
            lines=1,
            content="import logging\\n"
        )

        # INSERT: Add content after line 25
        result = await file_edit_lines(
            project_path=".",
            file_path="src/models.py",
            operation="insert",
            lines=25,
            content="    new_field: str",
            insert_after=True
        )

    Best Practice:
        - Use "delete" for removing debug code, unused imports
        - Use "replace" for updating blocks of code
        - Use "insert" for adding new code at specific locations
        - For semantic code changes, prefer symbol.replace or symbol.insert
    """
    try:
        paths = get_project_paths(project_path)
        base_path = paths["root"]
        full_path = base_path / file_path

        if not full_path.exists():
            return {
                "success": False,
                "operation": operation,
                "error": f"File not found: {file_path}"
            }

        # Read file
        file_content = full_path.read_text(encoding="utf-8")
        original_lines = file_content.splitlines(keepends=True)
        total_lines = len(original_lines)

        if operation == "delete":
            return await _delete_lines(full_path, original_lines, total_lines, lines)

        elif operation == "replace":
            if start_line is None or end_line is None:
                return {
                    "success": False,
                    "operation": "replace",
                    "error": "start_line and end_line required for replace operation"
                }
            if content is None:
                return {
                    "success": False,
                    "operation": "replace",
                    "error": "content required for replace operation"
                }
            return await _replace_lines(full_path, original_lines, total_lines, start_line, end_line, content)

        elif operation == "insert":
            if lines is None or not isinstance(lines, int):
                return {
                    "success": False,
                    "operation": "insert",
                    "error": "lines must be a single line number for insert operation"
                }
            if content is None:
                return {
                    "success": False,
                    "operation": "insert",
                    "error": "content required for insert operation"
                }
            return await _insert_lines(full_path, original_lines, total_lines, lines, content, insert_after)

        else:
            return {
                "success": False,
                "error": f"Unknown operation: {operation}. Use 'delete', 'replace', or 'insert'"
            }

    except Exception as e:
        return {
            "success": False,
            "operation": operation,
            "error": f"Failed to edit lines: {str(e)}"
        }


async def _delete_lines(
    full_path: Path,
    original_lines: List[str],
    total_lines: int,
    lines: Union[int, List[int], str, None]
) -> Dict[str, Any]:
    """Delete specified lines from file."""
    if lines is None:
        return {
            "success": False,
            "operation": "delete",
            "error": "lines parameter required for delete operation"
        }

    # Parse line numbers to delete
    lines_to_delete = set()

    if isinstance(lines, int):
        lines_to_delete.add(lines)
    elif isinstance(lines, list):
        lines_to_delete.update(lines)
    elif isinstance(lines, str):
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
                        "operation": "delete",
                        "error": f"Invalid range format: {part}"
                    }
            else:
                try:
                    lines_to_delete.add(int(part))
                except ValueError:
                    return {
                        "success": False,
                        "operation": "delete",
                        "error": f"Invalid line number: {part}"
                    }

    # Filter to valid line numbers
    valid_lines = {ln for ln in lines_to_delete if 1 <= ln <= total_lines}

    if not valid_lines:
        return {
            "success": True,
            "operation": "delete",
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
        "operation": "delete",
        "file_path": str(full_path),
        "lines_deleted": len(valid_lines),
        "deleted_content": "\n".join(deleted_content),
        "original_line_count": total_lines,
        "new_line_count": len(new_lines),
        "message": f"Deleted {len(valid_lines)} line(s)"
    }


async def _replace_lines(
    full_path: Path,
    original_lines: List[str],
    total_lines: int,
    start_line: int,
    end_line: int,
    content: str
) -> Dict[str, Any]:
    """Replace a range of lines with new content."""
    # Validate line numbers
    if start_line < 1:
        return {
            "success": False,
            "operation": "replace",
            "error": f"start_line must be >= 1, got {start_line}"
        }

    if end_line < start_line:
        return {
            "success": False,
            "operation": "replace",
            "error": f"end_line ({end_line}) must be >= start_line ({start_line})"
        }

    if start_line > total_lines:
        return {
            "success": False,
            "operation": "replace",
            "error": f"start_line ({start_line}) exceeds file length ({total_lines})"
        }

    # Adjust end_line if beyond file
    end_line = min(end_line, total_lines)

    # Extract replaced content
    replaced_lines = original_lines[start_line - 1:end_line]
    replaced_content = "".join(replaced_lines)

    # Prepare new content with proper line endings
    new_content_lines = content.splitlines(keepends=True)
    if new_content_lines and not new_content_lines[-1].endswith("\n"):
        new_content_lines[-1] += "\n"

    # Build new file content
    result_lines = (
        original_lines[:start_line - 1] +
        new_content_lines +
        original_lines[end_line:]
    )

    # Write new content
    new_file_content = "".join(result_lines)
    full_path.write_text(new_file_content, encoding="utf-8")

    lines_replaced = end_line - start_line + 1
    lines_inserted = len(new_content_lines)

    return {
        "success": True,
        "operation": "replace",
        "file_path": str(full_path),
        "lines_replaced": lines_replaced,
        "lines_inserted": lines_inserted,
        "line_range": f"{start_line}-{end_line}",
        "replaced_content": replaced_content.rstrip(),
        "message": f"Replaced {lines_replaced} line(s) with {lines_inserted} line(s)"
    }


async def _insert_lines(
    full_path: Path,
    original_lines: List[str],
    total_lines: int,
    line: int,
    content: str,
    insert_after: bool
) -> Dict[str, Any]:
    """Insert content at a specific line."""
    # Validate line number
    if line < 1:
        return {
            "success": False,
            "operation": "insert",
            "error": f"Line number must be >= 1, got {line}"
        }

    # Prepare content to insert
    insert_content_lines = content.splitlines(keepends=True)
    if insert_content_lines and not insert_content_lines[-1].endswith("\n"):
        insert_content_lines[-1] += "\n"

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
    new_lines = original_lines[:insert_idx] + insert_content_lines + original_lines[insert_idx:]

    # Write new content
    new_content = "".join(new_lines)
    full_path.write_text(new_content, encoding="utf-8")

    return {
        "success": True,
        "operation": "insert",
        "file_path": str(full_path),
        "inserted_at": actual_line,
        "lines_inserted": len(insert_content_lines),
        "original_line_count": total_lines,
        "new_line_count": len(new_lines),
        "insert_after": insert_after,
        "message": f"Inserted {len(insert_content_lines)} line(s) at line {actual_line}"
    }
