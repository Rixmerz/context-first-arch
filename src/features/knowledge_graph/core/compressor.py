"""
Content Compressor for Project Knowledge Graph.

Provides progressive disclosure through compression levels:
- Level 0 (FULL): Complete content with all comments
- Level 1 (NO_COMMENTS): Code without comments
- Level 2 (SIGNATURE_DOCSTRING): Signature + docstring only
- Level 3 (SIGNATURE_ONLY): Just the signature
"""

import re
from typing import Optional

from .models import CompressionLevel, KnowledgeChunk


def compress_chunk(
    chunk: KnowledgeChunk,
    level: CompressionLevel
) -> str:
    """
    Compress chunk content to specified level.

    Args:
        chunk: The knowledge chunk to compress
        level: Compression level

    Returns:
        Compressed content string
    """
    if level == CompressionLevel.FULL:
        return chunk.content

    if level == CompressionLevel.NO_COMMENTS:
        return strip_comments(chunk.content, _detect_language(chunk))

    if level == CompressionLevel.SIGNATURE_DOCSTRING:
        if chunk.signature:
            result = chunk.signature
            if chunk.docstring:
                result += f'\n    """{chunk.docstring}"""\n    ...'
            else:
                result += "\n    ..."
            return result
        # Fallback to content-based extraction
        return extract_signature_docstring(chunk.content, _detect_language(chunk))

    if level == CompressionLevel.SIGNATURE_ONLY:
        if chunk.signature:
            return chunk.signature + "\n    ..."
        return extract_signature(chunk.content, _detect_language(chunk))

    return chunk.content


def strip_comments(content: str, language: str) -> str:
    """
    Remove comments from code content.

    Args:
        content: Source code content
        language: Programming language

    Returns:
        Code without comments
    """
    lines = content.split("\n")
    result_lines = []
    in_multiline_comment = False  # For JS/TS block comments only
    in_python_multiline = False   # Track Python multiline strings (to preserve them)

    for line in lines:
        stripped = line.strip()

        if language == "python":
            # Skip single-line comments
            if stripped.startswith("#") and not stripped.startswith("#!"):
                continue

            # Handle docstrings and multiline strings (keep them, they're code/documentation)
            if '"""' in stripped or "'''" in stripped:
                # Toggle multiline state
                count = stripped.count('"""') + stripped.count("'''")
                if count % 2 == 1:
                    in_python_multiline = not in_python_multiline
                # Keep docstrings/multiline strings
                result_lines.append(line)
                continue

            # If inside a Python multiline string, keep the content
            if in_python_multiline:
                result_lines.append(line)
                continue

        elif language in ("javascript", "typescript"):
            # Skip single-line comments
            if stripped.startswith("//"):
                continue

            # Handle block comments
            if "/*" in stripped:
                if "*/" in stripped:
                    # Single-line block comment - remove it
                    line = re.sub(r'/\*.*?\*/', '', line)
                    if line.strip():
                        result_lines.append(line)
                    continue
                else:
                    in_multiline_comment = True
                    continue

            if in_multiline_comment:
                if "*/" in stripped:
                    in_multiline_comment = False
                continue

        elif language == "rust":
            # Skip single-line comments
            if stripped.startswith("//"):
                continue

            # Handle block comments
            if "/*" in stripped:
                if "*/" in stripped:
                    line = re.sub(r'/\*.*?\*/', '', line)
                    if line.strip():
                        result_lines.append(line)
                    continue
                else:
                    in_multiline_comment = True
                    continue

            if in_multiline_comment:
                if "*/" in stripped:
                    in_multiline_comment = False
                continue

        if not in_multiline_comment:
            result_lines.append(line)

    return "\n".join(result_lines)


def extract_signature_docstring(content: str, language: str) -> str:
    """
    Extract function/class signature and docstring only.

    Args:
        content: Source code content
        language: Programming language

    Returns:
        Signature + docstring + ellipsis
    """
    lines = content.split("\n")

    if language == "python":
        return _extract_python_signature_docstring(lines)
    elif language in ("javascript", "typescript"):
        return _extract_js_signature_docstring(lines)
    elif language == "rust":
        return _extract_rust_signature_docstring(lines)

    # Fallback: first few lines
    return "\n".join(lines[:5]) + "\n    ..."


def extract_signature(content: str, language: str) -> str:
    """
    Extract just the function/class signature.

    Args:
        content: Source code content
        language: Programming language

    Returns:
        Signature line + ellipsis
    """
    lines = content.split("\n")

    if language == "python":
        return _extract_python_signature(lines)
    elif language in ("javascript", "typescript"):
        return _extract_js_signature(lines)
    elif language == "rust":
        return _extract_rust_signature(lines)

    # Fallback: first line
    return lines[0] + "\n    ..." if lines else "..."


def _detect_language(chunk: KnowledgeChunk) -> str:
    """Detect language from chunk."""
    if chunk.file_path:
        ext = chunk.file_path.split(".")[-1].lower()
        lang_map = {
            "py": "python",
            "js": "javascript",
            "ts": "typescript",
            "tsx": "typescript",
            "jsx": "javascript",
            "rs": "rust",
            "go": "go",
            "java": "java",
            "rb": "ruby",
        }
        return lang_map.get(ext, "unknown")

    # Check tags
    for tag in chunk.tags:
        if tag in ("python", "javascript", "typescript", "rust", "go", "java"):
            return tag

    return "unknown"


def _extract_python_signature_docstring(lines: list) -> str:
    """Extract Python function/class signature and docstring."""
    result = []
    in_docstring = False
    docstring_delimiter = None

    for i, line in enumerate(lines):
        stripped = line.strip()

        # First line should be def/class
        if i == 0:
            result.append(line)
            continue

        # Check for docstring start
        if not in_docstring:
            if stripped.startswith('"""') or stripped.startswith("'''"):
                in_docstring = True
                docstring_delimiter = stripped[:3]
                result.append(line)

                # Check if docstring ends on same line
                if stripped.endswith(docstring_delimiter) and len(stripped) > 3:
                    in_docstring = False
                continue

            # If we hit code before docstring, stop
            if stripped and not stripped.startswith("#"):
                break

        # In docstring
        if in_docstring:
            result.append(line)
            if stripped.endswith(docstring_delimiter):
                in_docstring = False
                break

    result.append("    ...")
    return "\n".join(result)


def _extract_python_signature(lines: list) -> str:
    """Extract just Python signature."""
    if not lines:
        return "..."

    # Handle multi-line signatures
    signature_lines = []
    paren_count = 0

    for line in lines:
        signature_lines.append(line)
        paren_count += line.count("(") - line.count(")")

        if paren_count <= 0 and ":" in line:
            break

    return "\n".join(signature_lines) + "\n    ..."


def _extract_js_signature_docstring(lines: list) -> str:
    """Extract JavaScript/TypeScript signature and JSDoc."""
    result = []
    in_jsdoc = False

    for i, line in enumerate(lines):
        stripped = line.strip()

        # Capture JSDoc
        if stripped.startswith("/**"):
            in_jsdoc = True
            result.append(line)
            if stripped.endswith("*/"):
                in_jsdoc = False
            continue

        if in_jsdoc:
            result.append(line)
            if stripped.endswith("*/"):
                in_jsdoc = False
            continue

        # Capture function signature
        if ("function" in stripped or
            stripped.startswith("const ") or
            stripped.startswith("export ") or
            stripped.startswith("async ") or
            stripped.startswith("class ")):
            result.append(line)

            # Check for opening brace
            if "{" in stripped:
                break
            continue

        # Continue signature if it spans multiple lines
        if result and not "{" in stripped:
            result.append(line)
            if "{" in line:
                break

    result.append("  ...")
    return "\n".join(result)


def _extract_js_signature(lines: list) -> str:
    """Extract just JavaScript/TypeScript signature."""
    if not lines:
        return "..."

    signature_lines = []

    for line in lines:
        signature_lines.append(line)
        if "{" in line:
            break

    return "\n".join(signature_lines) + "\n  ..."


def _extract_rust_signature_docstring(lines: list) -> str:
    """Extract Rust function signature and doc comments."""
    result = []

    for i, line in enumerate(lines):
        stripped = line.strip()

        # Capture doc comments
        if stripped.startswith("///") or stripped.startswith("//!"):
            result.append(line)
            continue

        # Capture attributes
        if stripped.startswith("#["):
            result.append(line)
            continue

        # Capture function signature
        if ("fn " in stripped or
            "pub fn " in stripped or
            "struct " in stripped or
            "impl " in stripped):
            result.append(line)

            if "{" in stripped:
                break
            continue

        # Continue signature if needed
        if result and not "{" in stripped:
            result.append(line)
            if "{" in line:
                break

    result.append("    ...")
    return "\n".join(result)


def _extract_rust_signature(lines: list) -> str:
    """Extract just Rust signature."""
    if not lines:
        return "..."

    signature_lines = []

    for line in lines:
        stripped = line.strip()

        # Skip doc comments
        if stripped.startswith("///") or stripped.startswith("//!"):
            continue

        # Skip attributes (but keep them in signature)
        if stripped.startswith("#["):
            signature_lines.append(line)
            continue

        signature_lines.append(line)
        if "{" in line:
            break

    return "\n".join(signature_lines) + "\n    ..."


def estimate_compressed_tokens(
    chunk: KnowledgeChunk,
    level: CompressionLevel
) -> int:
    """
    Estimate token count at a compression level.

    Args:
        chunk: The chunk
        level: Compression level

    Returns:
        Estimated token count
    """
    if level == CompressionLevel.FULL:
        return chunk.token_count

    if level == CompressionLevel.NO_COMMENTS:
        # Estimate ~20% reduction
        return int(chunk.token_count * 0.8)

    if level == CompressionLevel.SIGNATURE_DOCSTRING:
        # Use compressed count if available
        if chunk.token_count_compressed:
            return chunk.token_count_compressed
        return int(chunk.token_count * 0.3)

    if level == CompressionLevel.SIGNATURE_ONLY:
        # Very minimal
        return int(chunk.token_count * 0.1)

    return chunk.token_count
