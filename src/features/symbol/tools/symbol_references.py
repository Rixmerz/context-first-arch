"""
MCP Tool: symbol.references

Find all references to a symbol at a specific location.
"""

from typing import Any, Dict

from src.features.symbol.core.symbols import find_references


async def symbol_references(
    project_path: str,
    file_path: str,
    line: int,
    column: int,
    context_lines: int = 2
) -> Dict[str, Any]:
    """
    Find all references to a symbol at a specific location.

    Uses LSP to find all usages of a symbol across the project.
    Requires precise line and column position of the symbol.

    Args:
        project_path: Path to the project root
        file_path: Relative path to the file containing the symbol
        line: Line number (1-indexed)
        column: Column number (1-indexed)
        context_lines: Number of context lines around each reference (default: 2)

    Returns:
        Dictionary with:
            - success: Boolean
            - symbol_name: Name of the symbol (if detected)
            - references: List of references with:
                - file_path: File containing the reference
                - line: Line number
                - column: Column number
                - context: Surrounding code snippet
            - count: Number of references found
            - files_affected: Number of unique files with references
            - mode: "lsp" or "fallback"

    Example:
        # Find references to symbol at line 45, column 10
        result = await symbol_references(
            project_path="/projects/my-app",
            file_path="src/services/user.py",
            line=45,
            column=10
        )

        # Find references with more context
        result = await symbol_references(
            project_path="/projects/my-app",
            file_path="src/models/order.py",
            line=12,
            column=5,
            context_lines=5
        )

    Usage tips:
        1. Use symbol.find first to locate the symbol
        2. Use the returned line/column to find references
        3. Useful for understanding impact before refactoring
    """
    try:
        result = find_references(
            project_path=project_path,
            file_path=file_path,
            line=line,
            column=column,
            context_lines=context_lines
        )

        return result

    except FileNotFoundError as e:
        return {
            "success": False,
            "error": f"File not found: {str(e)}"
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to find references: {str(e)}"
        }
