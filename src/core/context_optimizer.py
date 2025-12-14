"""
Context optimization for LLM token limits.

Compresses files while preserving essential information.
"""

import re
from dataclasses import dataclass
from typing import Any, List, Optional

# Try to import tiktoken, fallback to approximation if unavailable
try:
    import tiktoken
    TIKTOKEN_AVAILABLE = True
except ImportError:
    TIKTOKEN_AVAILABLE = False


@dataclass
class OptimizationResult:
    """Results of context optimization."""
    original_content: str
    optimized_content: str
    original_tokens: int
    optimized_tokens: int
    reduction_percentage: float
    strategies_applied: List[str]
    preserves_functionality: bool


def optimize_for_tokens(
    content: str,
    file_analysis: Any,
    max_tokens: int,
    model: str = "gpt-4"
) -> OptimizationResult:
    """
    Optimize file content to fit within token limit.

    Applies compression strategies in order until content fits:
    1. Remove comments (preserve docstrings)
    2. Compress whitespace
    3. Extract function signatures only
    4. Summarize implementation details

    Args:
        content: Original file content
        file_analysis: FileAnalysis object with metadata
        max_tokens: Maximum token count
        model: Model name for token counting (default: "gpt-4")

    Returns:
        OptimizationResult with optimized content and metadata
    """
    original_tokens = count_tokens(content, model)

    if original_tokens <= max_tokens:
        # No optimization needed
        return OptimizationResult(
            original_content=content,
            optimized_content=content,
            original_tokens=original_tokens,
            optimized_tokens=original_tokens,
            reduction_percentage=0.0,
            strategies_applied=[],
            preserves_functionality=True
        )

    # Apply optimization strategies
    strategies_applied = []
    current_content = content
    preserves_functionality = True

    # Strategy 1: Remove comments (keep docstrings)
    if count_tokens(current_content, model) > max_tokens:
        current_content = remove_comments(current_content, file_analysis.language)
        strategies_applied.append("remove_comments")

    # Strategy 2: Compress whitespace
    if count_tokens(current_content, model) > max_tokens:
        current_content = compress_whitespace(current_content)
        strategies_applied.append("compress_whitespace")

    # Strategy 3: Extract function signatures
    if count_tokens(current_content, model) > max_tokens:
        current_content = extract_signatures(file_analysis)
        strategies_applied.append("extract_signatures")
        preserves_functionality = False  # Only signatures, not full implementation

    # Strategy 4: Summarize (last resort)
    if count_tokens(current_content, model) > max_tokens:
        current_content = summarize_file(file_analysis)
        strategies_applied.append("summarize")
        preserves_functionality = False

    final_tokens = count_tokens(current_content, model)
    reduction = ((original_tokens - final_tokens) / original_tokens * 100) if original_tokens > 0 else 0

    return OptimizationResult(
        original_content=content,
        optimized_content=current_content,
        original_tokens=original_tokens,
        optimized_tokens=final_tokens,
        reduction_percentage=reduction,
        strategies_applied=strategies_applied,
        preserves_functionality=preserves_functionality
    )


def count_tokens(text: str, model: str = "gpt-4") -> int:
    """
    Count tokens in text.

    Uses tiktoken if available, otherwise approximates.
    """
    if TIKTOKEN_AVAILABLE:
        try:
            encoding = tiktoken.encoding_for_model(model)
            return len(encoding.encode(text))
        except Exception:
            # Fallback if model not found
            pass

    # Approximation: ~4 characters per token
    return len(text) // 4


def remove_comments(content: str, language: str) -> str:
    """
    Remove comments while preserving docstrings.

    Handles:
        Python: # comments, preserve triple-quoted docstrings
        JavaScript/TypeScript: // and /* */ comments, preserve JSDoc
        Rust: // and /* */ comments, preserve doc comments
    """
    if language == "python":
        lines = []
        in_docstring = False
        docstring_char = None

        for line in content.split("\n"):
            stripped = line.strip()

            # Check for docstring start/end
            if '"""' in stripped or "'''" in stripped:
                if '"""' in stripped:
                    docstring_char = '"""'
                else:
                    docstring_char = "'''"

                if stripped.count(docstring_char) >= 2:
                    # Single-line docstring
                    lines.append(line)
                else:
                    # Multi-line docstring
                    in_docstring = not in_docstring
                    lines.append(line)
            elif in_docstring:
                lines.append(line)
            elif not stripped.startswith("#"):
                # Not a comment line
                # Remove inline comments
                if "#" in line:
                    code_part = line.split("#")[0]
                    if code_part.strip():
                        lines.append(code_part.rstrip())
                else:
                    lines.append(line)

        return "\n".join(lines)

    elif language in ["javascript", "typescript"]:
        # Remove single-line comments (except JSDoc)
        content = re.sub(r'(?<!:)//(?! @).*$', '', content, flags=re.MULTILINE)

        # Remove multi-line comments (except JSDoc /** */)
        content = re.sub(r'/\*(?!\*).*?\*/', '', content, flags=re.DOTALL)

        return content

    elif language == "rust":
        # Preserve doc comments (///, //!)
        # Remove regular comments (//, /* */)
        lines = []
        for line in content.split("\n"):
            if not line.strip().startswith("//") or line.strip().startswith("///") or line.strip().startswith("//!"):
                lines.append(line)

        return "\n".join(lines)

    return content


def compress_whitespace(content: str) -> str:
    """
    Compress excessive whitespace.

    - Remove blank lines (keep max 1 consecutive blank line)
    - Remove trailing whitespace
    - Normalize indentation
    """
    # Remove trailing whitespace
    lines = [line.rstrip() for line in content.split("\n")]

    # Compress consecutive blank lines
    compressed = []
    prev_blank = False

    for line in lines:
        is_blank = not line.strip()

        if is_blank:
            if not prev_blank:
                compressed.append(line)
            prev_blank = True
        else:
            compressed.append(line)
            prev_blank = False

    return "\n".join(compressed)


def extract_signatures(file_analysis: Any) -> str:
    """
    Extract function signatures only.

    Returns a summary with function declarations but no implementations.
    """
    lines = []

    # File header
    lines.append(f"# {file_analysis.path} (signatures only)\n")

    # Imports
    if file_analysis.imports:
        lines.append("## Imports")
        for imp in file_analysis.imports[:10]:  # Limit imports
            if imp.is_default:
                lines.append(f"- import {imp.alias or imp.module} from '{imp.module}'")
            elif imp.names:
                lines.append(f"- import {{ {', '.join(imp.names[:5])} }} from '{imp.module}'")
        lines.append("")

    # Function signatures
    if file_analysis.functions:
        lines.append("## Functions")
        for func in file_analysis.functions:
            if func.is_exported:
                marker = "export "
            else:
                marker = ""

            if func.docstring:
                # Include brief docstring
                doc_lines = func.docstring.split("\n")[:2]  # First 2 lines only
                lines.append(f"// {doc_lines[0]}")

            lines.append(f"{marker}{func.signature}")
            lines.append("")

    return "\n".join(lines)


def summarize_file(file_analysis: Any) -> str:
    """
    Generate a minimal summary of the file.

    Last resort for very large files.
    """
    lines = []

    lines.append(f"# {file_analysis.path} (summary)")
    lines.append("")

    # Exports
    if file_analysis.exports:
        lines.append(f"Exports: {', '.join(file_analysis.exports[:20])}")

    # Function count
    if file_analysis.functions:
        exported = sum(1 for f in file_analysis.functions if f.is_exported)
        lines.append(f"Functions: {len(file_analysis.functions)} total, {exported} exported")

    # Types
    if file_analysis.types:
        lines.append(f"Types: {', '.join(file_analysis.types[:10])}")

    # Import summary
    if file_analysis.imports:
        lines.append(f"Imports: {len(file_analysis.imports)} modules")

    return "\n".join(lines)
