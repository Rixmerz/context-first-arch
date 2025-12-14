"""
TypeScript/JavaScript code analyzer.

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
    import tree_sitter_javascript
    import tree_sitter_typescript
    TREE_SITTER_AVAILABLE = True
except ImportError:
    TREE_SITTER_AVAILABLE = False


class TypeScriptAnalyzer(LanguageAnalyzer):
    """Analyzer for TypeScript files."""

    def __init__(self, is_typescript: bool = True):
        self._is_typescript = is_typescript
        self._parser = None

        if TREE_SITTER_AVAILABLE:
            self._parser = tree_sitter.Parser()
            if is_typescript:
                lang = tree_sitter_typescript.language_typescript()
            else:
                lang = tree_sitter_javascript.language()
            self._parser.language = lang

    @property
    def language(self) -> str:
        return "typescript" if self._is_typescript else "javascript"

    @property
    def extensions(self) -> List[str]:
        if self._is_typescript:
            return [".ts", ".tsx"]
        return [".js", ".jsx", ".mjs", ".cjs"]

    def analyze_file(self, file_path: Path) -> FileAnalysis:
        """Analyze a TypeScript/JavaScript file."""
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

        functions = self._extract_functions_ts(root, source, file_path)
        imports = self._extract_imports_ts(root, source)
        exports = self._extract_exports_ts(root, source)
        types = self._extract_types_ts(root, source)
        entry_points = self._find_entry_points_ts(functions, exports)

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

        # Extract imports
        import_patterns = [
            r'import\s+(?:(\w+)\s*,?\s*)?(?:\{([^}]+)\})?\s*from\s*[\'"]([^\'"]+)[\'"]',
            r'import\s+(\w+)\s+from\s*[\'"]([^\'"]+)[\'"]',
            r'const\s+(\w+)\s*=\s*require\s*\(\s*[\'"]([^\'"]+)[\'"]\s*\)',
        ]

        for pattern in import_patterns:
            for match in re.finditer(pattern, source):
                module = None
                if len(match.groups()) >= 3:
                    module = match.group(3)
                elif len(match.groups()) >= 2:
                    module = match.group(2)
                if module:
                    imports.append(ImportInfo(module=module, names=[]))

        # Extract functions
        func_patterns = [
            r'(?:export\s+)?(?:async\s+)?function\s+(\w+)\s*\(([^)]*)\)(?:\s*:\s*([^{]+))?',
            r'(?:export\s+)?const\s+(\w+)\s*=\s*(?:async\s+)?\(([^)]*)\)(?:\s*:\s*([^=]+))?\s*=>',
        ]

        for pattern in func_patterns:
            for match in re.finditer(pattern, source):
                name = match.group(1)
                params_str = match.group(2) if len(match.groups()) >= 2 else ""
                return_type = match.group(3).strip() if len(match.groups()) >= 3 and match.group(3) else None

                is_async = "async" in match.group(0)
                is_exported = "export" in match.group(0)
                start_line = source[:match.start()].count("\n") + 1

                functions.append(FunctionInfo(
                    name=name,
                    file_path=str(file_path),
                    start_line=start_line,
                    end_line=start_line,
                    signature=match.group(0).split("{")[0].strip(),
                    is_async=is_async,
                    is_exported=is_exported,
                    return_type=return_type
                ))

                if is_exported:
                    exports.append(name)

        return FileAnalysis(
            path=str(file_path),
            language=self.language,
            functions=functions,
            imports=imports,
            exports=exports,
            errors=["Using regex fallback - tree-sitter not available"]
        )

    def _extract_functions_ts(
        self,
        root,
        source: str,
        file_path: Path
    ) -> List[FunctionInfo]:
        """Extract functions using tree-sitter."""
        functions = []

        def visit(node, depth=0):
            is_func = node.type in [
                "function_declaration",
                "arrow_function",
                "function_expression",
                "method_definition"
            ]

            if is_func and depth < 2:
                func_info = self._parse_function_node(node, source, file_path)
                if func_info:
                    functions.append(func_info)

            for child in node.children:
                new_depth = depth + 1 if node.type in ["class_body", "object"] else depth
                visit(child, new_depth)

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
        is_exported = False

        # Check for export
        parent = node.parent
        if parent and parent.type in ["export_statement", "export_default_declaration"]:
            is_exported = True

        # Find function name
        for child in node.children:
            if child.type == "identifier":
                name = source[child.start_byte:child.end_byte]
                break
            elif child.type == "property_identifier":
                name = source[child.start_byte:child.end_byte]
                break

        # Check for async
        code_text = source[node.start_byte:node.end_byte]
        if "async" in code_text[:50]:
            is_async = True

        # Arrow functions in variable declarations
        if not name and node.type == "arrow_function":
            if parent and parent.type == "variable_declarator":
                for sibling in parent.children:
                    if sibling.type == "identifier":
                        name = source[sibling.start_byte:sibling.end_byte]
                        break

        if not name:
            return None

        start_line = source[:node.start_byte].count("\n") + 1
        end_line = source[:node.end_byte].count("\n") + 1

        # Extract calls
        calls = self._extract_calls_from_node(node, source)

        return FunctionInfo(
            name=name,
            file_path=str(file_path),
            start_line=start_line,
            end_line=end_line,
            signature=code_text.split("{")[0].strip()[:200],
            is_async=is_async,
            is_exported=is_exported,
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
                    if "." in call_name:
                        call_name = call_name.split(".")[-1]
                    calls.append(call_name)

            for child in n.children:
                visit(child)

        visit(node)
        return list(set(calls))

    def _extract_imports_ts(self, root, source: str) -> List[ImportInfo]:
        """Extract imports using tree-sitter."""
        imports = []

        def visit(node):
            if node.type == "import_statement":
                info = ImportInfo(module="", names=[])

                for child in node.children:
                    if child.type == "string":
                        info.module = source[child.start_byte:child.end_byte].strip("'\"")
                    elif child.type == "import_clause":
                        for subchild in child.children:
                            if subchild.type == "identifier":
                                info.names.append(source[subchild.start_byte:subchild.end_byte])
                                info.is_default = True
                            elif subchild.type == "named_imports":
                                for spec in subchild.children:
                                    if spec.type == "import_specifier":
                                        name = source[spec.start_byte:spec.end_byte]
                                        info.names.append(name.split(" as ")[0].strip())

                if info.module:
                    imports.append(info)

            for child in node.children:
                visit(child)

        visit(root)
        return imports

    def _extract_exports_ts(self, root, source: str) -> List[str]:
        """Extract exported symbols."""
        exports = []

        def visit(node):
            if node.type in ["export_statement", "export_default_declaration"]:
                for child in node.children:
                    if child.type == "identifier":
                        exports.append(source[child.start_byte:child.end_byte])
                    elif child.type in ["function_declaration", "class_declaration"]:
                        for subchild in child.children:
                            if subchild.type == "identifier":
                                exports.append(source[subchild.start_byte:subchild.end_byte])
                                break

            for child in node.children:
                visit(child)

        visit(root)
        return exports

    def _extract_types_ts(self, root, source: str) -> List[str]:
        """Extract type definitions."""
        types = []

        def visit(node):
            if node.type in ["interface_declaration", "type_alias_declaration"]:
                for child in node.children:
                    if child.type == "type_identifier":
                        types.append(source[child.start_byte:child.end_byte])
                        break

            for child in node.children:
                visit(child)

        visit(root)
        return types

    def _find_entry_points_ts(
        self,
        functions: List[FunctionInfo],
        exports: List[str]
    ) -> List[str]:
        """Find entry point functions."""
        entry_names = {"main", "handler", "app", "server", "default"}
        entry_points = []

        for func in functions:
            name_lower = func.name.lower()
            if name_lower in entry_names or func.name in exports:
                entry_points.append(func.name)

        return entry_points


class JavaScriptAnalyzer(TypeScriptAnalyzer):
    """Analyzer for JavaScript files."""

    def __init__(self):
        super().__init__(is_typescript=False)
