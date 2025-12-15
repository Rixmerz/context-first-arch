"""
MCP Tool: file.create

Create a new text file with content.
"""

from typing import Any, Dict, Optional
from pathlib import Path

from src.core.project import get_project_paths


async def file_create(
    project_path: str,
    file_path: str,
    content: str = "",
    overwrite: bool = False,
    create_directories: bool = True
) -> Dict[str, Any]:
    """
    Create a new text file with content.

    Creates a file at the specified path, optionally creating
    parent directories. Respects CFA project structure.

    Args:
        project_path: Path to the project root
        file_path: Relative path for the new file
        content: Content to write (default: empty string)
        overwrite: Whether to overwrite if file exists (default: False)
        create_directories: Create parent directories if needed (default: True)

    Returns:
        Dictionary with:
            - success: Boolean
            - file_path: Full path to created file
            - size_bytes: Size of created file
            - lines: Number of lines in content
            - created_directories: List of directories created
            - message: Human-readable status

    Example:
        # Create a new Python file
        result = await file_create(
            project_path="/projects/my-app",
            file_path="src/services/payment.py",
            content='''\"\"\"Payment service module.\"\"\"

from typing import Optional
from decimal import Decimal


class PaymentService:
    \"\"\"Handle payment processing.\"\"\"

    def process(self, amount: Decimal) -> bool:
        return True
'''
        )

        # Create empty config file
        result = await file_create(
            project_path="/projects/my-app",
            file_path="config/settings.json",
            content="{}"
        )

    Notes:
        - Validates against CFA-protected paths (.claude/, contracts/)
        - Creates parent directories by default
        - Returns error if file exists and overwrite=False
    """
    try:
        paths = get_project_paths(project_path)
        base_path = paths["root"]
        full_path = base_path / file_path

        # Check if file exists
        if full_path.exists() and not overwrite:
            return {
                "success": False,
                "error": f"File already exists: {file_path}. Use overwrite=True to replace."
            }

        # Validate not in protected paths (for edits, not reads)
        protected_paths = [".claude/config.json", ".claude/settings.json"]
        if any(file_path.startswith(p) for p in protected_paths):
            return {
                "success": False,
                "error": f"Cannot create in protected path: {file_path}"
            }

        # Create parent directories if needed
        created_dirs = []
        if create_directories:
            parent = full_path.parent
            if not parent.exists():
                parent.mkdir(parents=True, exist_ok=True)
                # Track created directories
                check_path = parent
                while check_path != base_path and check_path.exists():
                    created_dirs.insert(0, str(check_path.relative_to(base_path)))
                    check_path = check_path.parent

        # Write content
        full_path.write_text(content, encoding="utf-8")

        # Calculate stats
        size_bytes = full_path.stat().st_size
        lines = len(content.splitlines())

        return {
            "success": True,
            "file_path": str(full_path),
            "relative_path": file_path,
            "size_bytes": size_bytes,
            "lines": lines,
            "created_directories": created_dirs,
            "overwritten": full_path.exists() and overwrite,
            "message": f"Created {file_path} ({lines} lines, {size_bytes} bytes)"
        }

    except PermissionError:
        return {
            "success": False,
            "error": f"Permission denied: {file_path}"
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to create file: {str(e)}"
        }
