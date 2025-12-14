"""
MCP Tool: symbol.insert_after

Insert content after a symbol.
"""

from typing import Any, Dict

from src.core.lsp.symbols import insert_after_symbol


async def symbol_insert_after(
    project_path: str,
    file_path: str,
    symbol_name: str,
    content: str
) -> Dict[str, Any]:
    """
    Insert content immediately after a symbol definition.

    Useful for adding new functions/methods after existing ones,
    or appending related code after a class or function.

    Args:
        project_path: Path to the project root
        file_path: Relative path to the file containing the symbol
        symbol_name: Name of the symbol to insert after
        content: Code to insert (will be properly indented)

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
        # Add a new method after an existing one
        result = await symbol_insert_after(
            project_path="/projects/my-app",
            file_path="src/services/user.py",
            symbol_name="get_user",
            content='''
def get_user_by_email(self, email: str) -> Optional[User]:
    \"\"\"Get user by email address.\"\"\"
    return self.db.query(User).filter(User.email == email).first()
'''
        )

        # Add a helper function after another function
        result = await symbol_insert_after(
            project_path="/projects/my-app",
            file_path="src/utils/validators.py",
            symbol_name="validate_email",
            content='''
def validate_phone(phone: str) -> bool:
    \"\"\"Validate phone number format.\"\"\"
    import re
    return bool(re.match(r'^\\+?[1-9]\\d{1,14}$', phone))
'''
        )

    Notes:
        - Content indentation is preserved relative to the file
        - A blank line is automatically added between the symbol and new content
        - Works with functions, classes, methods
    """
    try:
        result = insert_after_symbol(
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
            "error": f"Failed to insert after symbol: {str(e)}"
        }
