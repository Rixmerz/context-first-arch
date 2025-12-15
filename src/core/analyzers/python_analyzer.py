"""
Python code analyzer using AST.

Extracts functions, imports, types, and entry points.
"""

import ast
from pathlib import Path
from typing import List, Optional, Dict, Any

from src.core.analyzers.base import (
    LanguageAnalyzer,
    FileAnalysis,
    FunctionInfo,
    ClassInfo,
    ImportInfo,
)


class PythonAnalyzer(LanguageAnalyzer):
    """Analyzer for Python files using AST."""

    @property
    def language(self) -> str:
        return "python"

    @property
    def extensions(self) -> List[str]:
        return [".py"]

    def analyze_file(self, file_path: Path) -> FileAnalysis:
        """Analyze a Python file."""
        try:
            source = file_path.read_text(encoding="utf-8")
            tree = ast.parse(source, filename=str(file_path))
        except SyntaxError as e:
            return FileAnalysis(
                path=str(file_path),
                language=self.language,
                errors=[f"Syntax error: {e}"]
            )
        except Exception as e:
            return FileAnalysis(
                path=str(file_path),
                language=self.language,
                errors=[f"Parse error: {e}"]
            )

        functions = self._extract_functions(tree, source, file_path)
        classes = self._extract_classes(tree, source, file_path)
        imports = self._extract_imports(tree)
        exports = self._extract_exports(tree)
        types = self._extract_types(tree)
        entry_points = self._find_entry_points(tree, functions)

        return FileAnalysis(
            path=str(file_path),
            language=self.language,
            functions=functions,
            classes=classes,
            imports=imports,
            exports=exports,
            types=types,
            entry_points=entry_points
        )

    def _extract_functions(
        self,
        tree: ast.AST,
        source: str,
        file_path: Path
    ) -> List[FunctionInfo]:
        """Extract all function definitions."""
        functions = []
        source_lines = source.split("\n")

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                # Get signature
                params = self._get_parameters(node)
                return_type = self._get_return_type(node)

                # Build signature string
                param_str = ", ".join(
                    f"{p['name']}: {p['type']}" if p.get('type') else p['name']
                    for p in params
                )
                sig = f"def {node.name}({param_str})"
                if return_type:
                    sig += f" -> {return_type}"

                # Get docstring
                docstring = ast.get_docstring(node)

                # Get function calls
                calls = self._extract_calls(node)

                functions.append(FunctionInfo(
                    name=node.name,
                    file_path=str(file_path),
                    start_line=node.lineno,
                    end_line=node.end_lineno or node.lineno,
                    signature=sig,
                    docstring=docstring,
                    is_async=isinstance(node, ast.AsyncFunctionDef),
                    is_exported=not node.name.startswith("_"),
                    calls=calls,
                    parameters=params,
                    return_type=return_type
                ))

        return functions

    def _extract_classes(
        self,
        tree: ast.AST,
        source: str,
        file_path: Path
    ) -> List[ClassInfo]:
        """Extract all class definitions (top-level only)."""
        classes = []
        source_lines = source.split("\n")

        for node in ast.iter_child_nodes(tree):
            if isinstance(node, ast.ClassDef):
                # Get base classes
                base_classes = []
                for base in node.bases:
                    try:
                        base_classes.append(ast.unparse(base))
                    except Exception:
                        pass

                # Build signature string
                bases_str = ", ".join(base_classes)
                sig = f"class {node.name}({bases_str})" if bases_str else f"class {node.name}"

                # Get docstring
                docstring = ast.get_docstring(node)

                # Get method names (direct children only)
                methods = []
                for child in node.body:
                    if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        methods.append(child.name)

                # Get decorators
                decorators = []
                for decorator in node.decorator_list:
                    try:
                        decorators.append(ast.unparse(decorator))
                    except Exception:
                        pass

                classes.append(ClassInfo(
                    name=node.name,
                    file_path=str(file_path),
                    start_line=node.lineno,
                    end_line=node.end_lineno or node.lineno,
                    signature=sig,
                    docstring=docstring,
                    base_classes=base_classes,
                    methods=methods,
                    is_exported=not node.name.startswith("_"),
                    decorators=decorators
                ))

        return classes

    def _get_parameters(self, node: ast.FunctionDef) -> List[Dict[str, str]]:
        """Extract function parameters with types."""
        params = []

        for arg in node.args.args:
            param = {"name": arg.arg}
            if arg.annotation:
                param["type"] = ast.unparse(arg.annotation)
            params.append(param)

        return params

    def _get_return_type(self, node: ast.FunctionDef) -> Optional[str]:
        """Extract return type annotation."""
        if node.returns:
            return ast.unparse(node.returns)
        return None

    def _extract_calls(self, node: ast.FunctionDef) -> List[str]:
        """Extract function calls within a function."""
        calls = []

        for child in ast.walk(node):
            if isinstance(child, ast.Call):
                if isinstance(child.func, ast.Name):
                    calls.append(child.func.id)
                elif isinstance(child.func, ast.Attribute):
                    calls.append(child.func.attr)

        return list(set(calls))

    def _extract_imports(self, tree: ast.AST) -> List[ImportInfo]:
        """Extract import statements."""
        imports = []

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(ImportInfo(
                        module=alias.name,
                        names=[],
                        alias=alias.asname
                    ))
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.append(ImportInfo(
                        module=node.module,
                        names=[alias.name for alias in node.names],
                        alias=None
                    ))

        return imports

    def _extract_exports(self, tree: ast.AST) -> List[str]:
        """Extract exported symbols (__all__ or public functions)."""
        exports = []

        for node in ast.walk(tree):
            # Check for __all__
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name) and target.id == "__all__":
                        if isinstance(node.value, ast.List):
                            for elt in node.value.elts:
                                if isinstance(elt, ast.Constant):
                                    exports.append(elt.value)

            # Public functions (not starting with _)
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if not node.name.startswith("_"):
                    if node.name not in exports:
                        exports.append(node.name)

            # Public classes
            if isinstance(node, ast.ClassDef):
                if not node.name.startswith("_"):
                    if node.name not in exports:
                        exports.append(node.name)

        return exports

    def _extract_types(self, tree: ast.AST) -> List[str]:
        """Extract type definitions (classes, TypedDict, etc.)."""
        types = []

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                types.append(node.name)

            # TypeAlias assignments
            if isinstance(node, ast.AnnAssign):
                if isinstance(node.target, ast.Name):
                    types.append(node.target.id)

        return types

    def _find_entry_points(
        self,
        tree: ast.AST,
        functions: List[FunctionInfo]
    ) -> List[str]:
        """Find entry point functions."""
        entry_points = []

        # Look for if __name__ == "__main__"
        for node in ast.walk(tree):
            if isinstance(node, ast.If):
                if isinstance(node.test, ast.Compare):
                    if isinstance(node.test.left, ast.Name):
                        if node.test.left.id == "__name__":
                            entry_points.append("__main__")

        # Common entry point names
        entry_names = {"main", "run", "start", "handler", "app", "cli"}
        for func in functions:
            if func.name.lower() in entry_names:
                entry_points.append(func.name)

        return list(set(entry_points))
