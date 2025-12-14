"""
MCP Tool: symbol.replace

Replace the body/implementation of a symbol.
"""

from typing import Any, Dict

from src.core.lsp.symbols import replace_symbol_body


async def symbol_replace(
    project_path: str,
    file_path: str,
    symbol_name: str,
    new_body: str
) -> Dict[str, Any]:
    """
    Replace the entire body/implementation of a symbol.

    Semantically replaces a function, method, or class body while
    preserving the signature and surrounding code.

    Args:
        project_path: Path to the project root
        file_path: Relative path to the file containing the symbol
        symbol_name: Name of the symbol to replace
        new_body: New implementation code

    Returns:
        Dictionary with:
            - success: Boolean
            - file_path: Modified file path
            - symbol_name: Name of replaced symbol
            - original_range: Line range of original symbol
            - new_range: Line range of new symbol
            - mode: "lsp" or "fallback"
            - message: Human-readable status

    Example:
        # Replace a function body
        result = await symbol_replace(
            project_path="/projects/my-app",
            file_path="src/utils/helpers.py",
            symbol_name="calculate_tax",
            new_body='''def calculate_tax(amount: float, rate: float = 0.1) -> float:
    \"\"\"Calculate tax with improved precision.\"\"\"
    return round(amount * rate, 2)'''
        )

        # Replace a method
        result = await symbol_replace(
            project_path="/projects/my-app",
            file_path="src/services/order.py",
            symbol_name="process_payment",
            new_body='''async def process_payment(self, order_id: str) -> PaymentResult:
    order = await self.get_order(order_id)
    result = await self.payment_gateway.charge(order.total)
    await self.update_order_status(order_id, "paid")
    return result'''
        )

    Important:
        - The new_body must include the complete function/method definition
        - Indentation should match the original context
        - Signature changes are allowed but may break references
    """
    try:
        result = replace_symbol_body(
            project_path=project_path,
            file_path=file_path,
            symbol_name=symbol_name,
            new_body=new_body
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
            "error": f"Failed to replace symbol: {str(e)}"
        }
