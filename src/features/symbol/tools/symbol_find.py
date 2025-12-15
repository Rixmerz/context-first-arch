"""
MCP Tool: symbol.find

Find symbols (functions, classes, methods) in a project.
"""

from typing import Any, Dict, List, Optional

from src.features.symbol.core.symbols import find_symbol


async def symbol_find(
    project_path: str,
    symbol_name: str,
    file_path: Optional[str] = None,
    symbol_kind: Optional[str] = None,
    include_body: bool = False,
    max_results: int = 50
) -> Dict[str, Any]:
    """
    Find symbols (functions, classes, methods, variables) in a project.

    Uses LSP for semantic accuracy when available, falls back to
    regex-based search for broader compatibility.

    Args:
        project_path: Path to the project root
        symbol_name: Name of the symbol to find (supports partial match)
        file_path: Optional - limit search to specific file
        symbol_kind: Optional - filter by kind: "function", "class", "method",
                     "variable", "property", "interface", "enum"
        include_body: Whether to include the symbol's body/implementation
        max_results: Maximum number of results to return (default: 50)

    Returns:
        Dictionary with:
            - success: Boolean
            - symbols: List of found symbols with:
                - name: Symbol name
                - kind: Symbol type (function, class, etc.)
                - file_path: File containing the symbol
                - line: Start line number
                - column: Start column
                - end_line: End line number
                - end_column: End column
                - container: Parent symbol (if any)
                - body: Symbol body (if include_body=True)
            - count: Number of symbols found
            - truncated: Whether results were truncated
            - mode: "lsp" or "fallback"

    Example:
        # Find all symbols named "User"
        result = await symbol_find(
            project_path="/projects/my-app",
            symbol_name="User"
        )

        # Find only classes named "Handler"
        result = await symbol_find(
            project_path="/projects/my-app",
            symbol_name="Handler",
            symbol_kind="class",
            include_body=True
        )

        # Find symbols in a specific file
        result = await symbol_find(
            project_path="/projects/my-app",
            symbol_name="process",
            file_path="src/services/worker.py"
        )
    """
    try:
        result = find_symbol(
            project_path=project_path,
            symbol_name=symbol_name,
            file_path=file_path,
            symbol_kind=symbol_kind,
            include_body=include_body,
            max_results=max_results
        )

        return result

    except FileNotFoundError as e:
        return {
            "success": False,
            "error": f"Path not found: {str(e)}"
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Symbol search failed: {str(e)}"
        }
