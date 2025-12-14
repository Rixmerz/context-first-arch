"""
MCP Tool: symbol.insert

Insert content before or after a symbol.
Consolidates: symbol.insert_before + symbol.insert_after
"""

from typing import Any, Dict, Literal

from src.core.lsp.symbols import insert_before_symbol, insert_after_symbol


async def symbol_insert(
    project_path: str,
    file_path: str,
    symbol_name: str,
    content: str,
    position: Literal["before", "after"] = "after"
) -> Dict[str, Any]:
    """
    Insert content before or after a symbol definition.

    Semantic code insertion that understands symbol boundaries.
    Use position="before" for decorators, comments, imports.
    Use position="after" for new functions, methods, related code.

    Args:
        project_path: Path to the project root
        file_path: Relative path to the file containing the symbol
        symbol_name: Name of the symbol to insert relative to
        content: Code to insert
        position: "before" or "after" the symbol (default: "after")

    Returns:
        Dictionary with:
            - success: Boolean
            - file_path: Modified file path
            - symbol_name: Reference symbol name
            - position: "before" or "after"
            - inserted_at_line: Line where content was inserted
            - lines_inserted: Number of lines inserted
            - mode: "lsp" or "fallback"
            - message: Human-readable status

    Examples:
        # Add decorator before function (position="before")
        result = await symbol_insert(
            project_path="/projects/my-app",
            file_path="src/api/routes.py",
            symbol_name="get_users",
            content='@require_auth',
            position="before"
        )

        # Add new method after existing one (position="after")
        result = await symbol_insert(
            project_path="/projects/my-app",
            file_path="src/services/user.py",
            symbol_name="get_user",
            content='''
def get_user_by_email(self, email: str) -> Optional[User]:
    return self.db.query(User).filter(User.email == email).first()
''',
            position="after"
        )

        # Add comment/imports before class (position="before")
        result = await symbol_insert(
            project_path="/projects/my-app",
            file_path="src/models/order.py",
            symbol_name="Order",
            content='# Order model for e-commerce\\nfrom typing import Optional',
            position="before"
        )

    Best Practice:
        - Use position="before" for: decorators, comments, type hints, imports
        - Use position="after" for: new functions, helper methods, related code
        - Blank line is automatically added between symbol and content
    """
    try:
        if position == "before":
            result = insert_before_symbol(
                project_path=project_path,
                file_path=file_path,
                symbol_name=symbol_name,
                content=content
            )
        elif position == "after":
            result = insert_after_symbol(
                project_path=project_path,
                file_path=file_path,
                symbol_name=symbol_name,
                content=content
            )
        else:
            return {
                "success": False,
                "error": f"Invalid position: {position}. Use 'before' or 'after'"
            }

        # Add position to result
        result["position"] = position
        return result

    except FileNotFoundError as e:
        return {
            "success": False,
            "position": position,
            "error": f"File not found: {str(e)}"
        }
    except ValueError as e:
        return {
            "success": False,
            "position": position,
            "error": f"Symbol not found: {str(e)}"
        }
    except Exception as e:
        return {
            "success": False,
            "position": position,
            "error": f"Failed to insert {position} symbol: {str(e)}"
        }
