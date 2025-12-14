"""
Symbol operations using LSP.

Provides high-level functions for semantic code operations:
- Symbol discovery and search
- Reference tracking
- Code modifications at symbol level
"""

import re
from pathlib import Path
from typing import Any, Dict, List, Optional

from src.core.lsp.manager import (
    LSPManager,
    Symbol,
    SymbolKind,
    Reference,
    get_lsp_manager,
)


def find_symbol(
    project_path: str,
    symbol_name: str,
    file_path: Optional[str] = None,
    symbol_kind: Optional[str] = None,
    include_body: bool = False,
    max_results: int = 50,
) -> Dict[str, Any]:
    """
    Find symbols by name using LSP.

    Performs global or file-scoped symbol search with filtering.

    Args:
        project_path: Path to CFA project
        symbol_name: Symbol name or pattern to search
        file_path: Optional file to scope search
        symbol_kind: Optional kind filter (function, class, method, etc.)
        include_body: Include symbol body in results
        max_results: Maximum number of results

    Returns:
        Dictionary with symbols found
    """
    manager = get_lsp_manager(project_path)
    path = Path(project_path)

    symbols = []

    # If LSP available, use it
    if getattr(manager, "_lsp_available", False):
        # Use LSP workspace/symbol search
        for lang, server in manager._servers.items():
            try:
                results = server.request_workspace_symbol(symbol_name)
                for sym in results[:max_results]:
                    parsed = _parse_lsp_symbol(sym, path, include_body)
                    if parsed and _matches_filter(parsed, symbol_kind):
                        symbols.append(parsed)
            except Exception:
                continue
    else:
        # Fallback: regex-based search
        symbols = _fallback_find_symbol(
            path, symbol_name, file_path, symbol_kind, include_body, max_results
        )

    return {
        "success": True,
        "count": len(symbols),
        "symbols": [s.to_dict() for s in symbols[:max_results]],
        "lsp_mode": getattr(manager, "_lsp_available", False),
    }


def find_references(
    project_path: str,
    file_path: str,
    line: int,
    column: int,
    context_lines: int = 2,
) -> Dict[str, Any]:
    """
    Find all references to a symbol at the given position.

    Args:
        project_path: Path to CFA project
        file_path: File containing the symbol
        line: Line number (1-indexed)
        column: Column number (1-indexed)
        context_lines: Lines of context around each reference

    Returns:
        Dictionary with references found
    """
    manager = get_lsp_manager(project_path)
    path = Path(project_path)
    full_path = path / file_path

    references = []

    if getattr(manager, "_lsp_available", False):
        server = manager.get_server(full_path)
        if server:
            try:
                results = server.request_references(
                    str(full_path), line - 1, column - 1
                )
                for ref in results:
                    parsed = _parse_lsp_reference(ref, path, context_lines)
                    if parsed:
                        references.append(parsed)
            except Exception as e:
                return {"success": False, "error": str(e)}
    else:
        # Fallback: Find symbol name at position and grep
        references = _fallback_find_references(
            path, full_path, line, column, context_lines
        )

    return {
        "success": True,
        "count": len(references),
        "references": [r.to_dict() for r in references],
        "lsp_mode": getattr(manager, "_lsp_available", False),
    }


def get_symbols_overview(
    project_path: str,
    file_path: str,
    max_depth: int = 2,
    max_chars: int = 5000,
) -> Dict[str, Any]:
    """
    Get overview of symbols defined in a file.

    Args:
        project_path: Path to CFA project
        file_path: File to analyze
        max_depth: Maximum nesting depth to show
        max_chars: Maximum characters in result

    Returns:
        Dictionary with symbol hierarchy
    """
    manager = get_lsp_manager(project_path)
    path = Path(project_path)
    full_path = path / file_path

    if not full_path.exists():
        return {"success": False, "error": f"File not found: {file_path}"}

    symbols = []

    if getattr(manager, "_lsp_available", False):
        server = manager.get_server(full_path)
        if server:
            try:
                results = server.request_document_symbol(str(full_path))
                symbols = _parse_document_symbols(results, path, max_depth)
            except Exception:
                pass

    if not symbols:
        # Fallback: Parse file for symbol definitions
        symbols = _fallback_get_overview(full_path, max_depth)

    # Format overview
    overview = _format_symbols_overview(symbols, max_chars)

    return {
        "success": True,
        "file": file_path,
        "symbol_count": len(symbols),
        "overview": overview,
        "symbols": [s.to_dict() for s in symbols],
        "lsp_mode": getattr(manager, "_lsp_available", False),
    }


def replace_symbol_body(
    project_path: str,
    file_path: str,
    symbol_name: str,
    new_body: str,
) -> Dict[str, Any]:
    """
    Replace the complete body of a symbol.

    Args:
        project_path: Path to CFA project
        file_path: File containing the symbol
        symbol_name: Name of symbol to replace
        new_body: New content for the symbol

    Returns:
        Dictionary with result of operation
    """
    path = Path(project_path)
    full_path = path / file_path

    if not full_path.exists():
        return {"success": False, "error": f"File not found: {file_path}"}

    # Find symbol location
    result = find_symbol(project_path, symbol_name, file_path, include_body=True)

    if not result["symbols"]:
        return {"success": False, "error": f"Symbol not found: {symbol_name}"}

    symbol = result["symbols"][0]

    # Read file
    content = full_path.read_text()
    lines = content.splitlines(keepends=True)

    # Replace lines
    start_line = symbol["line"] - 1
    end_line = symbol["end_line"]

    new_lines = lines[:start_line] + [new_body + "\n"] + lines[end_line:]
    new_content = "".join(new_lines)

    # Write back
    full_path.write_text(new_content)

    return {
        "success": True,
        "file": file_path,
        "symbol": symbol_name,
        "lines_replaced": end_line - start_line,
        "message": f"Replaced {symbol_name} body",
    }


def insert_after_symbol(
    project_path: str,
    file_path: str,
    symbol_name: str,
    content: str,
) -> Dict[str, Any]:
    """
    Insert content after a symbol definition.

    Args:
        project_path: Path to CFA project
        file_path: File containing the symbol
        symbol_name: Name of symbol to insert after
        content: Content to insert

    Returns:
        Dictionary with result of operation
    """
    path = Path(project_path)
    full_path = path / file_path

    if not full_path.exists():
        return {"success": False, "error": f"File not found: {file_path}"}

    # Find symbol
    result = find_symbol(project_path, symbol_name, file_path)

    if not result["symbols"]:
        return {"success": False, "error": f"Symbol not found: {symbol_name}"}

    symbol = result["symbols"][0]
    insert_line = symbol["end_line"]

    # Read and modify
    file_content = full_path.read_text()
    lines = file_content.splitlines(keepends=True)

    # Ensure content ends with newline
    if not content.endswith("\n"):
        content += "\n"

    # Insert after symbol
    lines.insert(insert_line, "\n" + content)
    new_content = "".join(lines)

    full_path.write_text(new_content)

    return {
        "success": True,
        "file": file_path,
        "inserted_after": symbol_name,
        "at_line": insert_line + 1,
        "message": f"Inserted content after {symbol_name}",
    }


def insert_before_symbol(
    project_path: str,
    file_path: str,
    symbol_name: str,
    content: str,
) -> Dict[str, Any]:
    """
    Insert content before a symbol definition.

    Args:
        project_path: Path to CFA project
        file_path: File containing the symbol
        symbol_name: Name of symbol to insert before
        content: Content to insert

    Returns:
        Dictionary with result of operation
    """
    path = Path(project_path)
    full_path = path / file_path

    if not full_path.exists():
        return {"success": False, "error": f"File not found: {file_path}"}

    # Find symbol
    result = find_symbol(project_path, symbol_name, file_path)

    if not result["symbols"]:
        return {"success": False, "error": f"Symbol not found: {symbol_name}"}

    symbol = result["symbols"][0]
    insert_line = symbol["line"] - 1

    # Read and modify
    file_content = full_path.read_text()
    lines = file_content.splitlines(keepends=True)

    # Ensure content ends with newline
    if not content.endswith("\n"):
        content += "\n"

    # Insert before symbol
    lines.insert(insert_line, content + "\n")
    new_content = "".join(lines)

    full_path.write_text(new_content)

    return {
        "success": True,
        "file": file_path,
        "inserted_before": symbol_name,
        "at_line": insert_line + 1,
        "message": f"Inserted content before {symbol_name}",
    }


def rename_symbol(
    project_path: str,
    file_path: str,
    old_name: str,
    new_name: str,
) -> Dict[str, Any]:
    """
    Rename a symbol throughout the codebase.

    Uses LSP refactoring when available, falls back to
    grep-and-replace.

    Args:
        project_path: Path to CFA project
        file_path: File containing the symbol definition
        old_name: Current symbol name
        new_name: New symbol name

    Returns:
        Dictionary with files modified
    """
    manager = get_lsp_manager(project_path)
    path = Path(project_path)
    full_path = path / file_path

    if not full_path.exists():
        return {"success": False, "error": f"File not found: {file_path}"}

    files_modified = []

    if getattr(manager, "_lsp_available", False):
        server = manager.get_server(full_path)
        if server:
            try:
                # Find symbol position
                result = find_symbol(project_path, old_name, file_path)
                if result["symbols"]:
                    symbol = result["symbols"][0]
                    edits = server.request_rename(
                        str(full_path),
                        symbol["line"] - 1,
                        symbol["column"] - 1,
                        new_name,
                    )
                    files_modified = _apply_rename_edits(path, edits)
            except Exception as e:
                return {"success": False, "error": f"LSP rename failed: {e}"}

    if not files_modified:
        # Fallback: find and replace
        files_modified = _fallback_rename(path, old_name, new_name)

    return {
        "success": True,
        "old_name": old_name,
        "new_name": new_name,
        "files_modified": files_modified,
        "count": len(files_modified),
        "lsp_mode": getattr(manager, "_lsp_available", False),
    }


# ============ Helper Functions ============


def _parse_lsp_symbol(lsp_symbol: Dict, project_path: Path, include_body: bool) -> Optional[Symbol]:
    """Parse an LSP symbol response into our Symbol type."""
    try:
        location = lsp_symbol.get("location", {})
        uri = location.get("uri", "")
        range_info = location.get("range", {})

        file_path = uri.replace("file://", "")
        try:
            file_path = str(Path(file_path).relative_to(project_path))
        except ValueError:
            pass

        start = range_info.get("start", {})
        end = range_info.get("end", {})

        body = None
        if include_body:
            try:
                full_path = project_path / file_path
                if full_path.exists():
                    lines = full_path.read_text().splitlines()
                    start_line = start.get("line", 0)
                    end_line = end.get("line", start_line) + 1
                    body = "\n".join(lines[start_line:end_line])
            except Exception:
                pass

        return Symbol(
            name=lsp_symbol.get("name", ""),
            kind=SymbolKind(lsp_symbol.get("kind", 1)),
            file_path=file_path,
            line=start.get("line", 0) + 1,
            column=start.get("character", 0) + 1,
            end_line=end.get("line", 0) + 1,
            end_column=end.get("character", 0) + 1,
            container=lsp_symbol.get("containerName"),
            body=body,
        )
    except Exception:
        return None


def _parse_lsp_reference(lsp_ref: Dict, project_path: Path, context_lines: int) -> Optional[Reference]:
    """Parse an LSP reference response."""
    try:
        uri = lsp_ref.get("uri", "")
        range_info = lsp_ref.get("range", {})

        file_path = uri.replace("file://", "")
        try:
            file_path = str(Path(file_path).relative_to(project_path))
        except ValueError:
            pass

        start = range_info.get("start", {})
        line = start.get("line", 0) + 1
        column = start.get("character", 0) + 1

        # Get context
        context = ""
        try:
            full_path = project_path / file_path
            if full_path.exists():
                lines = full_path.read_text().splitlines()
                start_ctx = max(0, line - 1 - context_lines)
                end_ctx = min(len(lines), line + context_lines)
                context = "\n".join(lines[start_ctx:end_ctx])
        except Exception:
            pass

        return Reference(
            file_path=file_path,
            line=line,
            column=column,
            context=context,
        )
    except Exception:
        return None


def _parse_document_symbols(lsp_symbols: List, project_path: Path, max_depth: int, depth: int = 0) -> List[Symbol]:
    """Parse document symbols from LSP response."""
    symbols = []

    if depth >= max_depth:
        return symbols

    for sym in lsp_symbols:
        try:
            range_info = sym.get("range", sym.get("location", {}).get("range", {}))
            start = range_info.get("start", {})
            end = range_info.get("end", {})

            symbols.append(Symbol(
                name=sym.get("name", ""),
                kind=SymbolKind(sym.get("kind", 1)),
                file_path="",
                line=start.get("line", 0) + 1,
                column=start.get("character", 0) + 1,
                end_line=end.get("line", 0) + 1,
                end_column=end.get("character", 0) + 1,
            ))

            # Recurse for children
            children = sym.get("children", [])
            if children:
                symbols.extend(_parse_document_symbols(children, project_path, max_depth, depth + 1))

        except Exception:
            continue

    return symbols


def _matches_filter(symbol: Symbol, kind_filter: Optional[str]) -> bool:
    """Check if symbol matches kind filter."""
    if not kind_filter:
        return True
    return symbol.kind.name.lower() == kind_filter.lower()


def _format_symbols_overview(symbols: List[Symbol], max_chars: int) -> str:
    """Format symbols into readable overview."""
    lines = []
    for sym in symbols:
        kind = sym.kind.name.lower()
        lines.append(f"  {kind}: {sym.name} (line {sym.line})")

    result = "\n".join(lines)
    if len(result) > max_chars:
        result = result[:max_chars] + "\n... (truncated)"

    return result


def _apply_rename_edits(project_path: Path, edits: Dict) -> List[str]:
    """Apply LSP rename edits to files."""
    files_modified = []

    for uri, file_edits in edits.get("changes", {}).items():
        file_path = uri.replace("file://", "")
        try:
            full_path = Path(file_path)
            content = full_path.read_text()

            # Apply edits in reverse order to preserve positions
            sorted_edits = sorted(
                file_edits,
                key=lambda e: (e["range"]["start"]["line"], e["range"]["start"]["character"]),
                reverse=True,
            )

            lines = content.splitlines(keepends=True)
            for edit in sorted_edits:
                start = edit["range"]["start"]
                end = edit["range"]["end"]
                new_text = edit["newText"]

                # Apply edit
                start_line = start["line"]
                end_line = end["line"]

                if start_line == end_line:
                    line = lines[start_line]
                    lines[start_line] = (
                        line[:start["character"]] +
                        new_text +
                        line[end["character"]:]
                    )

            full_path.write_text("".join(lines))
            rel_path = str(full_path.relative_to(project_path))
            files_modified.append(rel_path)

        except Exception:
            continue

    return files_modified


# ============ Fallback Functions (no LSP) ============


def _fallback_find_symbol(
    project_path: Path,
    pattern: str,
    file_path: Optional[str],
    kind_filter: Optional[str],
    include_body: bool,
    max_results: int,
) -> List[Symbol]:
    """Find symbols using regex when LSP unavailable."""
    symbols = []

    # Patterns for different symbol types
    patterns = {
        "function": [
            r"^(?:async\s+)?(?:export\s+)?function\s+(\w+)",  # JS/TS
            r"^(?:async\s+)?def\s+(\w+)",  # Python
            r"^(?:pub\s+)?(?:async\s+)?fn\s+(\w+)",  # Rust
        ],
        "class": [
            r"^(?:export\s+)?class\s+(\w+)",  # JS/TS
            r"^class\s+(\w+)",  # Python
            r"^(?:pub\s+)?struct\s+(\w+)",  # Rust
        ],
        "method": [
            r"^\s+(?:async\s+)?(\w+)\s*\([^)]*\)\s*[:{]",  # JS/TS method
            r"^\s+(?:async\s+)?def\s+(\w+)",  # Python method
        ],
    }

    # Determine search scope
    if file_path:
        search_paths = [project_path / file_path]
    else:
        search_paths = list(project_path.rglob("*"))
        # Filter to source files
        search_paths = [
            p for p in search_paths
            if p.is_file() and p.suffix in [".py", ".js", ".ts", ".tsx", ".jsx", ".rs"]
        ]

    for path in search_paths:
        try:
            content = path.read_text()
            lines = content.splitlines()

            for i, line in enumerate(lines):
                for kind, kind_patterns in patterns.items():
                    if kind_filter and kind != kind_filter:
                        continue

                    for p in kind_patterns:
                        match = re.match(p, line)
                        if match and pattern.lower() in match.group(1).lower():
                            # Find end of symbol
                            end_line = _find_symbol_end(lines, i)

                            body = None
                            if include_body:
                                body = "\n".join(lines[i:end_line + 1])

                            symbols.append(Symbol(
                                name=match.group(1),
                                kind=SymbolKind[kind.upper()],
                                file_path=str(path.relative_to(project_path)),
                                line=i + 1,
                                column=1,
                                end_line=end_line + 1,
                                end_column=len(lines[end_line]) if end_line < len(lines) else 1,
                                body=body,
                            ))

                            if len(symbols) >= max_results:
                                return symbols

        except Exception:
            continue

    return symbols


def _find_symbol_end(lines: List[str], start: int) -> int:
    """Find the end line of a symbol definition."""
    # Simple brace/indent matching
    if start >= len(lines):
        return start

    first_line = lines[start]

    # Check for brace-based languages
    if "{" in first_line:
        brace_count = first_line.count("{") - first_line.count("}")
        for i in range(start + 1, len(lines)):
            brace_count += lines[i].count("{") - lines[i].count("}")
            if brace_count <= 0:
                return i
        return len(lines) - 1

    # Check for indent-based (Python)
    if first_line.rstrip().endswith(":"):
        base_indent = len(first_line) - len(first_line.lstrip())
        for i in range(start + 1, len(lines)):
            line = lines[i]
            if line.strip() == "":
                continue
            current_indent = len(line) - len(line.lstrip())
            if current_indent <= base_indent:
                return i - 1
        return len(lines) - 1

    return start


def _fallback_find_references(
    project_path: Path,
    file_path: Path,
    line: int,
    column: int,
    context_lines: int,
) -> List[Reference]:
    """Find references using grep when LSP unavailable."""
    references = []

    # Get symbol name at position
    try:
        content = file_path.read_text()
        lines = content.splitlines()
        target_line = lines[line - 1] if line <= len(lines) else ""

        # Extract word at column
        words = re.findall(r"\w+", target_line)
        symbol = None
        pos = 0
        for word in words:
            idx = target_line.find(word, pos)
            if idx <= column - 1 <= idx + len(word):
                symbol = word
                break
            pos = idx + len(word)

        if not symbol:
            return references

        # Search all files
        for path in project_path.rglob("*"):
            if not path.is_file():
                continue
            if path.suffix not in [".py", ".js", ".ts", ".tsx", ".jsx", ".rs"]:
                continue

            try:
                file_content = path.read_text()
                file_lines = file_content.splitlines()

                for i, line_content in enumerate(file_lines):
                    if re.search(rf"\b{re.escape(symbol)}\b", line_content):
                        # Get context
                        start_ctx = max(0, i - context_lines)
                        end_ctx = min(len(file_lines), i + context_lines + 1)
                        context = "\n".join(file_lines[start_ctx:end_ctx])

                        references.append(Reference(
                            file_path=str(path.relative_to(project_path)),
                            line=i + 1,
                            column=line_content.find(symbol) + 1,
                            context=context,
                        ))

            except Exception:
                continue

    except Exception:
        pass

    return references


def _fallback_get_overview(file_path: Path, max_depth: int) -> List[Symbol]:
    """Get symbol overview using regex when LSP unavailable."""
    result = _fallback_find_symbol(
        file_path.parent,
        "",  # Match all
        str(file_path.name),
        None,  # All kinds
        False,
        100,
    )
    return result


def _fallback_rename(project_path: Path, old_name: str, new_name: str) -> List[str]:
    """Rename symbol using find-and-replace when LSP unavailable."""
    files_modified = []
    pattern = rf"\b{re.escape(old_name)}\b"

    for path in project_path.rglob("*"):
        if not path.is_file():
            continue
        if path.suffix not in [".py", ".js", ".ts", ".tsx", ".jsx", ".rs"]:
            continue

        try:
            content = path.read_text()
            if re.search(pattern, content):
                new_content = re.sub(pattern, new_name, content)
                path.write_text(new_content)
                files_modified.append(str(path.relative_to(project_path)))
        except Exception:
            continue

    return files_modified
