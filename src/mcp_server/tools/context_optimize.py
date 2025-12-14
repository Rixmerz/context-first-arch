"""
MCP Tool: context.optimize

Optimize file content for LLM token limits.
"""

from typing import Any, Dict
from pathlib import Path

from src.core.analyzers import get_registry
from src.core.context_optimizer import optimize_for_tokens


async def context_optimize(
    project_path: str,
    file_path: str,
    max_tokens: int = 4000,
    model: str = "gpt-4"
) -> Dict[str, Any]:
    """
    Optimize file content to fit within token limit.

    Applies intelligent compression strategies while preserving
    essential information. Useful for including large files in
    LLM context windows.

    Compression strategies (applied in order):
    1. Remove comments (preserve docstrings)
    2. Compress whitespace
    3. Extract function signatures only
    4. Summarize implementation

    Args:
        project_path: Path to CFA project
        file_path: Relative path to file (e.g., "impl/user.ts")
        max_tokens: Maximum token count (default: 4000)
        model: Model name for token counting (default: "gpt-4")

    Returns:
        Dictionary with:
            - success: Boolean
            - original_tokens: Token count before optimization
            - optimized_tokens: Token count after optimization
            - reduction_percentage: Percentage reduction
            - optimized_content: Compressed file content
            - strategies_applied: List of compression strategies used
            - preserves_functionality: Whether full code is preserved
            - warning: Optional warning about information loss

    Example:
        # Optimize large file for context window
        result = await context_optimize(
            project_path="/projects/my-app",
            file_path="impl/large_module.ts",
            max_tokens=4000
        )
    """
    try:
        path = Path(project_path)

        # Validate CFA project
        if not (path / ".claude").exists():
            return {"success": False, "error": "Not a CFA project (missing .claude/)"}

        # Normalize file path
        target_path = file_path
        if not target_path.startswith("impl/"):
            target_path = f"impl/{target_path}"

        full_path = path / target_path

        if not full_path.exists():
            return {
                "success": False,
                "error": f"File not found: {target_path}"
            }

        # Analyze file
        registry = get_registry()
        analyzer = registry.get_analyzer_for_file(full_path)

        if not analyzer:
            return {
                "success": False,
                "error": f"No analyzer available for: {full_path.suffix}",
                "hint": "Supported extensions: .ts, .tsx, .js, .jsx, .py, .rs"
            }

        try:
            analysis = analyzer.analyze_file(full_path)
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to analyze file: {str(e)}"
            }

        # Read original content
        try:
            original_content = full_path.read_text()
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to read file: {str(e)}"
            }

        # Validate max_tokens
        if max_tokens < 100:
            return {
                "success": False,
                "error": "max_tokens must be at least 100",
                "hint": "Recommended: 2000-8000 for meaningful content"
            }

        # Optimize content
        result = optimize_for_tokens(
            content=original_content,
            file_analysis=analysis,
            max_tokens=max_tokens,
            model=model
        )

        # Prepare response
        warning = None
        if not result.preserves_functionality:
            warning = (
                "⚠️ Full implementation not preserved. "
                "Only signatures/summary included due to token limit."
            )

        return {
            "success": True,
            "file_path": target_path,
            "original_tokens": result.original_tokens,
            "optimized_tokens": result.optimized_tokens,
            "reduction_percentage": round(result.reduction_percentage, 1),
            "optimized_content": result.optimized_content,
            "strategies_applied": result.strategies_applied,
            "preserves_functionality": result.preserves_functionality,
            "max_tokens": max_tokens,
            "model": model,
            "warning": warning,
            "summary": {
                "tokens_saved": result.original_tokens - result.optimized_tokens,
                "compression_ratio": f"{result.reduction_percentage:.1f}%",
                "fits_limit": result.optimized_tokens <= max_tokens
            },
            "message": _format_message(result, max_tokens)
        }

    except Exception as e:
        return {
            "success": False,
            "error": f"Context optimization failed: {str(e)}"
        }


def _format_message(result: Any, max_tokens: int) -> str:
    """Generate human-readable message."""
    if result.original_tokens <= max_tokens:
        return f"✓ No optimization needed ({result.original_tokens} tokens < {max_tokens} limit)"

    if result.optimized_tokens > max_tokens:
        return (
            f"⚠️ Still exceeds limit: {result.optimized_tokens} tokens "
            f"(target: {max_tokens}, reduced {result.reduction_percentage:.1f}%)"
        )

    strategies = ", ".join(result.strategies_applied)

    if result.preserves_functionality:
        return (
            f"✓ Optimized to {result.optimized_tokens} tokens "
            f"({result.reduction_percentage:.1f}% reduction, full code preserved) "
            f"via {strategies}"
        )
    else:
        return (
            f"⚠️ Optimized to {result.optimized_tokens} tokens "
            f"({result.reduction_percentage:.1f}% reduction, signatures only) "
            f"via {strategies}"
        )
