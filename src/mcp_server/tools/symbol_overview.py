"""
MCP Tool: symbol.overview

Get a hierarchical overview of symbols in a file.
"""

from typing import Any, Dict

from src.core.lsp.symbols import get_symbols_overview


async def symbol_overview(
    project_path: str,
    file_path: str,
    max_depth: int = 2,
    max_chars: int = 5000
) -> Dict[str, Any]:
    """
    Get a hierarchical overview of all symbols in a file.

    Provides a structured view of classes, functions, methods, and
    their relationships. Useful for understanding file structure
    before making modifications.

    Args:
        project_path: Path to the project root
        file_path: Relative path to the file to analyze
        max_depth: Maximum nesting depth to show (default: 2)
                   Use -1 for unlimited depth
        max_chars: Maximum characters in the overview (default: 5000)
                   Truncates if exceeded

    Returns:
        Dictionary with:
            - success: Boolean
            - file_path: Analyzed file path
            - overview: Formatted string with symbol hierarchy
            - symbols: List of top-level symbols with nested children
            - symbol_count: Total number of symbols found
            - truncated: Whether overview was truncated
            - mode: "lsp" or "fallback"

    Example:
        # Get overview of a Python file
        result = await symbol_overview(
            project_path="/projects/my-app",
            file_path="src/services/auth.py"
        )

        # Get deep overview with more detail
        result = await symbol_overview(
            project_path="/projects/my-app",
            file_path="src/models/user.py",
            max_depth=5,
            max_chars=10000
        )

    Output example:
        overview: '''
        class UserService:
            def __init__(self, db: Database)
            def get_user(self, user_id: str) -> User
            def create_user(self, data: UserCreate) -> User
            def update_user(self, user_id: str, data: UserUpdate) -> User

        class UserValidator:
            def validate_email(self, email: str) -> bool
            def validate_password(self, password: str) -> bool
        '''
    """
    try:
        result = get_symbols_overview(
            project_path=project_path,
            file_path=file_path,
            max_depth=max_depth,
            max_chars=max_chars
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
            "error": f"Failed to get symbol overview: {str(e)}"
        }
