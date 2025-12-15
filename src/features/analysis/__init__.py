"""
Analysis Feature - Code Analysis and Metrics

Language-aware code analysis for coupling, dependencies, impact, and patterns.
"""

from .core import (
    LanguageAnalyzer, AnalyzerRegistry, FileAnalysis,
    FunctionInfo, ClassInfo, ImportInfo, get_registry,
    PythonAnalyzer, TypeScriptAnalyzer, JavaScriptAnalyzer, RustAnalyzer,
    analyze_coupling, DependencyGraph, build_dependency_graph,
    get_dependencies, get_dependents, get_feature_dependencies,
    analyze_impact, detect_patterns,
)

__all__ = [
    "LanguageAnalyzer", "AnalyzerRegistry", "FileAnalysis",
    "FunctionInfo", "ClassInfo", "ImportInfo", "get_registry",
    "PythonAnalyzer", "TypeScriptAnalyzer", "JavaScriptAnalyzer", "RustAnalyzer",
    "analyze_coupling", "DependencyGraph", "build_dependency_graph",
    "get_dependencies", "get_dependents", "get_feature_dependencies",
    "analyze_impact", "detect_patterns",
]
