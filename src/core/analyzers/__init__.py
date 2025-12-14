"""
Code analyzers for Context-First Architecture.

Supports Python, TypeScript/JavaScript, and Rust.
"""

from src.core.analyzers.base import LanguageAnalyzer, AnalyzerRegistry
from src.core.analyzers.python_analyzer import PythonAnalyzer
from src.core.analyzers.typescript_analyzer import TypeScriptAnalyzer, JavaScriptAnalyzer
from src.core.analyzers.rust_analyzer import RustAnalyzer


def get_registry() -> AnalyzerRegistry:
    """Get analyzer registry with all supported languages."""
    registry = AnalyzerRegistry()
    registry.register(PythonAnalyzer())
    registry.register(TypeScriptAnalyzer())
    registry.register(JavaScriptAnalyzer())
    registry.register(RustAnalyzer())
    return registry


__all__ = [
    "LanguageAnalyzer",
    "AnalyzerRegistry",
    "PythonAnalyzer",
    "TypeScriptAnalyzer",
    "JavaScriptAnalyzer",
    "RustAnalyzer",
    "get_registry",
]
