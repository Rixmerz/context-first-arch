"""
Analysis Core Module - Code Analysis and Metrics

Provides language analyzers and code quality metrics.
"""

from .base import (
    LanguageAnalyzer, AnalyzerRegistry, FileAnalysis,
    FunctionInfo, ClassInfo, ImportInfo,
)
from .python_analyzer import PythonAnalyzer
from .typescript_analyzer import TypeScriptAnalyzer, JavaScriptAnalyzer
from .rust_analyzer import RustAnalyzer
from .coupling_analyzer import analyze_coupling
from .dependency_analyzer import (
    DependencyGraph, build_dependency_graph, get_dependencies, get_dependents,
    get_feature_dependencies,
)
from .impact_analyzer import analyze_impact
from .pattern_detector import detect_patterns


def get_registry() -> AnalyzerRegistry:
    """Get analyzer registry with all supported languages."""
    registry = AnalyzerRegistry()
    registry.register(PythonAnalyzer())
    registry.register(TypeScriptAnalyzer())
    registry.register(JavaScriptAnalyzer())
    registry.register(RustAnalyzer())
    return registry


__all__ = [
    # Base
    "LanguageAnalyzer", "AnalyzerRegistry", "FileAnalysis",
    "FunctionInfo", "ClassInfo", "ImportInfo",
    # Factory
    "get_registry",
    # Analyzers
    "PythonAnalyzer", "TypeScriptAnalyzer", "JavaScriptAnalyzer", "RustAnalyzer",
    # Analysis functions
    "analyze_coupling", "DependencyGraph", "build_dependency_graph",
    "get_dependencies", "get_dependents", "get_feature_dependencies",
    "analyze_impact", "detect_patterns",
]
