"""
MCP Tool: file.replace

Replace content in a file (literal or regex).
"""

from typing import Any, Dict, Optional
from pathlib import Path
import re

from src.core.project import get_project_paths


async def file_replace(
    project_path: str,
    file_path: str,
    search: str,
    replace: str,
    use_regex: bool = False,
    count: int = 0,
    case_sensitive: bool = True
) -> Dict[str, Any]:
    """
    Replace content in a file using literal or regex patterns.

    Performs search-and-replace operations with support for
    regular expressions and occurrence limiting.

    Args:
        project_path: Path to the project root
        file_path: Relative path to the file
        search: String or pattern to find
        replace: Replacement string (supports backreferences with regex)
        use_regex: Use regex matching (default: False)
        count: Max replacements (0 = all occurrences)
        case_sensitive: Case sensitive matching (default: True)

    Returns:
        Dictionary with:
            - success: Boolean
            - file_path: Modified file path
            - replacements_made: Number of replacements
            - original_content: First 500 chars of original (for verification)
            - message: Human-readable status

    Example:
        # Simple literal replacement
        result = await file_replace(
            project_path="/projects/my-app",
            file_path="src/config.py",
            search="DEBUG = True",
            replace="DEBUG = False"
        )

        # Case-insensitive replacement
        result = await file_replace(
            project_path="/projects/my-app",
            file_path="src/messages.py",
            search="error",
            replace="ERROR",
            case_sensitive=False
        )

        # Regex replacement with backreferences
        result = await file_replace(
            project_path="/projects/my-app",
            file_path="src/api.py",
            search=r"console\\.log\\((.*)\\)",
            replace=r"logger.debug(\\1)",
            use_regex=True
        )

        # Replace only first occurrence
        result = await file_replace(
            project_path="/projects/my-app",
            file_path="src/main.py",
            search="TODO",
            replace="DONE",
            count=1
        )

    Notes:
        - Creates a backup before modification (original content in response)
        - Regex uses Python re module syntax
        - Backreferences in replace: \\1, \\2, etc.
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

        # Read original content
        original = full_path.read_text(encoding="utf-8")

        # Perform replacement
        if use_regex:
            flags = 0 if case_sensitive else re.IGNORECASE
            try:
                pattern = re.compile(search, flags)
            except re.error as e:
                return {
                    "success": False,
                    "error": f"Invalid regex: {str(e)}"
                }

            if count > 0:
                new_content, replacements = pattern.subn(replace, original, count=count)
            else:
                new_content, replacements = pattern.subn(replace, original)
        else:
            if case_sensitive:
                if count > 0:
                    new_content = original.replace(search, replace, count)
                else:
                    new_content = original.replace(search, replace)
                replacements = original.count(search) if count == 0 else min(count, original.count(search))
            else:
                # Case-insensitive literal replacement
                pattern = re.compile(re.escape(search), re.IGNORECASE)
                if count > 0:
                    new_content, replacements = pattern.subn(replace, original, count=count)
                else:
                    new_content, replacements = pattern.subn(replace, original)

        if replacements == 0:
            return {
                "success": True,
                "file_path": str(full_path),
                "replacements_made": 0,
                "message": "No matches found - file unchanged"
            }

        # Write new content
        full_path.write_text(new_content, encoding="utf-8")

        return {
            "success": True,
            "file_path": str(full_path),
            "replacements_made": replacements,
            "original_preview": original[:500] + ("..." if len(original) > 500 else ""),
            "message": f"Made {replacements} replacement(s) in {file_path}"
        }

    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to replace content: {str(e)}"
        }
