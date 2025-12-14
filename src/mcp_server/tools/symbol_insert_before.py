"""
MCP Tool: symbol.insert_before

Insert content before a symbol.
"""

from typing import Any, Dict

from src.core.lsp.symbols import insert_before_symbol


async def symbol_insert_before(
    project_path: str,
    file_path: str,
    symbol_name: str,
    content: str
) -> Dict[str, Any]:
    """
    Insert content immediately before a symbol definition.

    Useful for adding decorators, comments, imports, or related
    code before an existing symbol.

    Args:
        project_path: Path to the project root
        file_path: Relative path to the file containing the symbol
        symbol_name: Name of the symbol to insert before
        content: Code to insert

    Returns:
        Dictionary with:
            - success: Boolean
            - file_path: Modified file path
            - symbol_name: Reference symbol name
            - inserted_at_line: Line where content was inserted
            - lines_inserted: Number of lines inserted
            - mode: "lsp" or "fallback"
            - message: Human-readable status

    Example:
        # Add a decorator before a function
        result = await symbol_insert_before(
            project_path="/projects/my-app",
            file_path="src/api/routes.py",
            symbol_name="get_users",
            content='@require_auth\\n@rate_limit(100)'
        )

        # Add a docstring/comment before a class
        result = await symbol_insert_before(
            project_path="/projects/my-app",
            file_path="src/models/order.py",
            symbol_name="Order",
            content='''# Order model for e-commerce transactions
# Supports multiple payment methods and shipping options
'''
        )

        # Add imports before a function that needs them
        result = await symbol_insert_before(
            project_path="/projects/my-app",
            file_path="src/utils/dates.py",
            symbol_name="parse_date",
            content='from datetime import datetime, timedelta\\nfrom typing import Optional'
        )

    Notes:
        - Content is inserted preserving its formatting
        - Useful for adding decorators, comments, or type hints
        - A blank line is added after the inserted content
    """
    try:
        result = insert_before_symbol(
            project_path=project_path,
            file_path=file_path,
            symbol_name=symbol_name,
            content=content
        )

        return result

    except FileNotFoundError as e:
        return {
            "success": False,
            "error": f"File not found: {str(e)}"
        }
    except ValueError as e:
        return {
            "success": False,
            "error": f"Symbol not found: {str(e)}"
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to insert before symbol: {str(e)}"
        }
