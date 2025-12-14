"""
Rust code analyzer.

Uses tree-sitter when available, falls back to regex.
Adapted from ASOA framework.
"""

import re
from pathlib import Path
from typing import List, Optional, Dict, Any

from src.core.analyzers.base import (
    LanguageAnalyzer,
    FileAnalysis,
    FunctionInfo,
    ImportInfo,
)

# Try to import tree-sitter
try:
    import tree_sitter
    import tree_sitter_rust
    TREE_SITTER_AVAILABLE = True
except ImportError:
    TREE_SITTER_AVAILABLE = False


class RustAnalyzer(LanguageAnalyzer):
    """Analyzer for Rust files."""

    def __init__(self):
        self._parser = None

        if TREE_SITTER_AVAILABLE:
            self._parser = tree_sitter.Parser()
            lang = tree_sitter_rust.language()
            self._parser.language = lang

    @property
    def language(self) -> str:
        return "rust"

    @property
    def extensions(self) -> List[str]:
        return [".rs"]

    def analyze_file(self, file_path: Path) -> FileAnalysis:
        """Analyze a Rust file."""
        try:
            source = file_path.read_text(encoding="utf-8")
        except Exception as e:
            return FileAnalysis(
                path=str(file_path),
                language=self.language,
                errors=[f"Read error: {e}"]
            )

        if TREE_SITTER_AVAILABLE and self._parser:
            return self._analyze_with_tree_sitter(source, file_path)
        else:
            return self._analyze_with_regex(source, file_path)

    def _analyze_with_tree_sitter(
        self,
        source: str,
        file_path: Path
    ) -> FileAnalysis:
        """Analyze using tree-sitter."""
        tree = self._parser.parse(bytes(source, "utf-8"))
        root = tree.root_node

        functions = self._extract_functions_rust(root, source, file_path)
        imports = self._extract_imports_rust(root, source)
        exports = self._extract_exports_rust(root, source)
        types = self._extract_types_rust(root, source)
        entry_points = self._find_entry_points_rust(functions)

        return FileAnalysis(
            path=str(file_path),
            language=self.language,
            functions=functions,
            imports=imports,
            exports=exports,
            types=types,
            entry_points=entry_points
        )

    def _analyze_with_regex(
        self,
        source: str,
        file_path: Path
    ) -> FileAnalysis:
        """Fallback regex-based analysis."""
        functions = []
        imports = []
        exports = []
        types = []

        # Extract use statements
        use_pattern = r'use\s+([\w:]+)(?:::\{([^}]+)\})?;'
        for match in re.finditer(use_pattern, source):
            module = match.group(1) or ""
            items = match.group(2).split(",") if match.group(2) else []
            imports.append(ImportInfo(
                module=module,
                names=[item.strip() for item in items if item.strip()]
            ))

        # Extract functions
        func_pattern = r'(?:pub\s+)?(?:async\s+)?fn\s+(\w+)\s*(?:<[^>]*>)?\s*\(([^)]*)\)(?:\s*->\s*([^{]+))?'
        for match in re.finditer(func_pattern, source):
            name = match.group(1)
            params = match.group(2) if match.group(2) else ""
            return_type = match.group(3).strip() if match.group(3) else None
            is_pub = "pub" in match.group(0)
            is_async = "async" in match.group(0)
            start_line = source[:match.start()].count("\n") + 1

            functions.append(FunctionInfo(
                name=name,
                file_path=str(file_path),
                start_line=start_line,
                end_line=start_line,
                signature=match.group(0).strip(),
                is_async=is_async,
                is_exported=is_pub,
                return_type=return_type
            ))

            if is_pub:
                exports.append(name)

        # Extract structs
        struct_pattern = r'(?:pub\s+)?struct\s+(\w+)'
        for match in re.finditer(struct_pattern, source):
            types.append(match.group(1))
            if "pub" in match.group(0):
                exports.append(match.group(1))

        # Extract enums
        enum_pattern = r'(?:pub\s+)?enum\s+(\w+)'
        for match in re.finditer(enum_pattern, source):
            types.append(match.group(1))
            if "pub" in match.group(0):
                exports.append(match.group(1))

        return FileAnalysis(
            path=str(file_path),
            language=self.language,
            functions=functions,
            imports=imports,
            exports=list(set(exports)),
            types=types,
            errors=["Using regex fallback - tree-sitter not available"]
        )

    def _extract_functions_rust(
        self,
        root,
        source: str,
        file_path: Path
    ) -> List[FunctionInfo]:
        """Extract functions using tree-sitter."""
        functions = []

        def visit(node, in_impl: bool = False):
            if node.type == "function_item":
                func_info = self._parse_function_node(node, source, file_path)
                if func_info:
                    functions.append(func_info)

            if node.type == "impl_item":
                for child in node.children:
                    visit(child, in_impl=True)
            else:
                for child in node.children:
                    visit(child, in_impl)

        visit(root)
        return functions

    def _parse_function_node(
        self,
        node,
        source: str,
        file_path: Path
    ) -> Optional[FunctionInfo]:
        """Parse a function node into FunctionInfo."""
        name = ""
        is_async = False
        is_pub = False

        code_text = source[node.start_byte:node.end_byte]

        for child in node.children:
            if child.type == "visibility_modifier":
                is_pub = True
            elif child.type == "identifier":
                name = source[child.start_byte:child.end_byte]

        if "async" in code_text[:50]:
            is_async = True

        if not name:
            return None

        start_line = source[:node.start_byte].count("\n") + 1
        end_line = source[:node.end_byte].count("\n") + 1

        # Extract signature (up to opening brace)
        signature = code_text.split("{")[0].strip()

        # Extract calls
        calls = self._extract_calls_from_node(node, source)

        return FunctionInfo(
            name=name,
            file_path=str(file_path),
            start_line=start_line,
            end_line=end_line,
            signature=signature[:200],
            is_async=is_async,
            is_exported=is_pub,
            calls=calls
        )

    def _extract_calls_from_node(self, node, source: str) -> List[str]:
        """Extract function calls from a node."""
        calls = []

        def visit(n):
            if n.type == "call_expression":
                func_node = n.children[0] if n.children else None
                if func_node:
                    call_name = source[func_node.start_byte:func_node.end_byte]
                    if "::" in call_name:
                        call_name = call_name.split("::")[-1]
                    if "." in call_name:
                        call_name = call_name.split(".")[-1]
                    calls.append(call_name)

            if n.type == "macro_invocation":
                for child in n.children:
                    if child.type == "identifier":
                        calls.append(source[child.start_byte:child.end_byte])
                        break

            for child in n.children:
                visit(child)

        visit(node)
        return list(set(calls))

    def _extract_imports_rust(self, root, source: str) -> List[ImportInfo]:
        """Extract use statements using tree-sitter."""
        imports = []

        def visit(node):
            if node.type == "use_declaration":
                info = ImportInfo(module="", names=[])

                for child in node.children:
                    if child.type in ["scoped_identifier", "identifier", "use_wildcard"]:
                        info.module = source[child.start_byte:child.end_byte]
                    elif child.type == "use_list":
                        for item in child.children:
                            if item.type in ["identifier", "scoped_identifier"]:
                                info.names.append(source[item.start_byte:item.end_byte])

                if info.module:
                    imports.append(info)

            for child in node.children:
                visit(child)

        visit(root)
        return imports

    def _extract_exports_rust(self, root, source: str) -> List[str]:
        """Extract public (exported) symbols."""
        exports = []

        def visit(node):
            has_pub = False
            name = None

            if node.type in ["function_item", "struct_item", "enum_item", "type_item"]:
                for child in node.children:
                    if child.type == "visibility_modifier":
                        has_pub = True
                    elif child.type in ["identifier", "type_identifier"]:
                        name = source[child.start_byte:child.end_byte]

                if has_pub and name:
                    exports.append(name)

            for child in node.children:
                visit(child)

        visit(root)
        return exports

    def _extract_types_rust(self, root, source: str) -> List[str]:
        """Extract type definitions (structs, enums)."""
        types = []

        def visit(node):
            if node.type in ["struct_item", "enum_item", "type_item"]:
                for child in node.children:
                    if child.type == "type_identifier":
                        types.append(source[child.start_byte:child.end_byte])
                        break

            for child in node.children:
                visit(child)

        visit(root)
        return types

    def _find_entry_points_rust(
        self,
        functions: List[FunctionInfo]
    ) -> List[str]:
        """Find entry point functions."""
        entry_points = []

        for func in functions:
            if func.name == "main":
                entry_points.append("main")
            elif "handler" in func.name.lower():
                entry_points.append(func.name)

        return entry_points
