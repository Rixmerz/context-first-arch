"""
Base class for language analyzers.

Adapted from ASOA framework for CFA.
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, List, Optional, Set
from dataclasses import dataclass, field


@dataclass
class FunctionInfo:
    """Information about an extracted function."""
    name: str
    file_path: str
    start_line: int
    end_line: int
    signature: str
    docstring: Optional[str] = None
    is_async: bool = False
    is_exported: bool = False
    calls: List[str] = field(default_factory=list)
    parameters: List[Dict[str, str]] = field(default_factory=list)
    return_type: Optional[str] = None


@dataclass
class ImportInfo:
    """Information about an import statement."""
    module: str
    names: List[str] = field(default_factory=list)
    alias: Optional[str] = None
    is_default: bool = False


@dataclass
class ClassInfo:
    """Information about an extracted class."""
    name: str
    file_path: str
    start_line: int
    end_line: int
    signature: str
    docstring: Optional[str] = None
    base_classes: List[str] = field(default_factory=list)
    methods: List[str] = field(default_factory=list)
    is_exported: bool = False
    decorators: List[str] = field(default_factory=list)


@dataclass
class FileAnalysis:
    """Complete analysis of a source file."""
    path: str
    language: str
    functions: List[FunctionInfo] = field(default_factory=list)
    classes: List[ClassInfo] = field(default_factory=list)
    imports: List[ImportInfo] = field(default_factory=list)
    exports: List[str] = field(default_factory=list)
    types: List[str] = field(default_factory=list)
    entry_points: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)


class LanguageAnalyzer(ABC):
    """Abstract base class for language-specific analyzers."""

    @property
    @abstractmethod
    def language(self) -> str:
        """Return the language this analyzer handles."""
        pass

    @property
    @abstractmethod
    def extensions(self) -> List[str]:
        """Return file extensions this analyzer can process."""
        pass

    def can_analyze(self, file_path: Path) -> bool:
        """Check if this analyzer can handle the file."""
        return file_path.suffix.lower() in self.extensions

    @abstractmethod
    def analyze_file(self, file_path: Path) -> FileAnalysis:
        """
        Analyze a source file.

        Returns FileAnalysis with:
        - functions: All functions with signatures, params, docstrings
        - imports: All import statements
        - exports: Exported symbols
        - types: Type definitions
        - entry_points: Main functions, handlers, etc.
        """
        pass

    def get_function_info(
        self,
        file_path: Path,
        function_name: str
    ) -> Optional[FunctionInfo]:
        """Get info for a specific function."""
        analysis = self.analyze_file(file_path)
        for func in analysis.functions:
            if func.name == function_name:
                return func
        return None


class AnalyzerRegistry:
    """Registry for language analyzers."""

    def __init__(self):
        self._analyzers: Dict[str, LanguageAnalyzer] = {}
        self._extension_map: Dict[str, LanguageAnalyzer] = {}

    def register(self, analyzer: LanguageAnalyzer) -> None:
        """Register a language analyzer."""
        self._analyzers[analyzer.language] = analyzer
        for ext in analyzer.extensions:
            self._extension_map[ext] = analyzer

    def get_analyzer(self, language: str) -> Optional[LanguageAnalyzer]:
        """Get analyzer for a specific language."""
        return self._analyzers.get(language.lower())

    def get_analyzer_for_file(self, file_path: Path) -> Optional[LanguageAnalyzer]:
        """Get appropriate analyzer based on file extension."""
        ext = file_path.suffix.lower()
        return self._extension_map.get(ext)

    def supported_extensions(self) -> Set[str]:
        """Return all supported file extensions."""
        return set(self._extension_map.keys())

    def supported_languages(self) -> Set[str]:
        """Return all supported languages."""
        return set(self._analyzers.keys())
