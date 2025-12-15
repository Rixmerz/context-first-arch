"""
MCP Tool: symbol.rename

Rename a symbol across the entire project.
"""

from typing import Any, Dict

from src.features.symbol.core.symbols import rename_symbol


async def symbol_rename(
    project_path: str,
    file_path: str,
    old_name: str,
    new_name: str
) -> Dict[str, Any]:
    """
    Rename a symbol across the entire project.

    Performs a semantic rename that updates all references to the symbol,
    including imports, type hints, and usages across files.

    Args:
        project_path: Path to the project root
        file_path: Relative path to the file containing the symbol definition
        old_name: Current name of the symbol
        new_name: New name for the symbol

    Returns:
        Dictionary with:
            - success: Boolean
            - old_name: Original symbol name
            - new_name: New symbol name
            - files_modified: List of files that were updated
            - occurrences_replaced: Total number of replacements made
            - mode: "lsp" or "fallback"
            - message: Human-readable status

    Example:
        # Rename a function
        result = await symbol_rename(
            project_path="/projects/my-app",
            file_path="src/services/user.py",
            old_name="getUserById",
            new_name="get_user_by_id"
        )

        # Rename a class
        result = await symbol_rename(
            project_path="/projects/my-app",
            file_path="src/models/user.py",
            old_name="UserModel",
            new_name="User"
        )

        # Rename a method
        result = await symbol_rename(
            project_path="/projects/my-app",
            file_path="src/services/order.py",
            old_name="processOrder",
            new_name="process_order"
        )

    Important:
        - Creates a backup of modified files (when using LSP)
        - Updates all references including imports and type hints
        - In fallback mode, uses regex which may miss some edge cases
        - Review changes after rename to ensure correctness

    Workflow:
        1. Use symbol.find to locate the symbol
        2. Use symbol.references to see all usages
        3. Use symbol.rename to perform the refactoring
        4. Run tests to verify correctness
    """
    try:
        result = rename_symbol(
            project_path=project_path,
            file_path=file_path,
            old_name=old_name,
            new_name=new_name
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
            "error": f"Failed to rename symbol: {str(e)}"
        }
