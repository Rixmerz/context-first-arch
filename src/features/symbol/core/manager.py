"""
LSP Manager - Wrapper for multilspy providing synchronous LSP operations.

Manages language server lifecycle and provides high-level API for
symbol operations across multiple programming languages.
"""

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional
from enum import Enum

logger = logging.getLogger("cfa.lsp")

# Language to LSP server mapping
LANGUAGE_SERVERS = {
    # Python
    ".py": "python",
    # JavaScript/TypeScript
    ".js": "typescript",
    ".jsx": "typescript",
    ".ts": "typescript",
    ".tsx": "typescript",
    # Rust
    ".rs": "rust",
    # Go
    ".go": "go",
    # Java
    ".java": "java",
    # C/C++
    ".c": "clangd",
    ".cpp": "clangd",
    ".h": "clangd",
    ".hpp": "clangd",
    # C#
    ".cs": "csharp",
    # Ruby
    ".rb": "ruby",
    # PHP
    ".php": "php",
}


class SymbolKind(Enum):
    """LSP Symbol kinds."""
    FILE = 1
    MODULE = 2
    NAMESPACE = 3
    PACKAGE = 4
    CLASS = 5
    METHOD = 6
    PROPERTY = 7
    FIELD = 8
    CONSTRUCTOR = 9
    ENUM = 10
    INTERFACE = 11
    FUNCTION = 12
    VARIABLE = 13
    CONSTANT = 14
    STRING = 15
    NUMBER = 16
    BOOLEAN = 17
    ARRAY = 18
    OBJECT = 19
    KEY = 20
    NULL = 21
    ENUM_MEMBER = 22
    STRUCT = 23
    EVENT = 24
    OPERATOR = 25
    TYPE_PARAMETER = 26


@dataclass
class Symbol:
    """Represents a code symbol."""
    name: str
    kind: SymbolKind
    file_path: str
    line: int
    column: int
    end_line: int
    end_column: int
    container: Optional[str] = None
    body: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "kind": self.kind.name.lower(),
            "file_path": self.file_path,
            "line": self.line,
            "column": self.column,
            "end_line": self.end_line,
            "end_column": self.end_column,
            "container": self.container,
            "body": self.body,
        }


@dataclass
class Reference:
    """Represents a symbol reference."""
    file_path: str
    line: int
    column: int
    context: str  # Surrounding code

    def to_dict(self) -> Dict[str, Any]:
        return {
            "file_path": self.file_path,
            "line": self.line,
            "column": self.column,
            "context": self.context,
        }


@dataclass
class LSPManager:
    """
    Manages LSP servers for a project.

    Provides synchronous access to language server features
    for semantic code analysis and modification.
    """
    project_path: Path
    _servers: Dict[str, Any] = field(default_factory=dict, repr=False)
    _initialized: bool = False

    def __post_init__(self):
        self.project_path = Path(self.project_path)

    def initialize(self) -> bool:
        """
        Initialize LSP servers for the project.

        Detects languages used in the project and starts
        appropriate language servers.
        """
        if self._initialized:
            return True

        try:
            # Try to import multilspy
            try:
                from multilspy import LanguageServer
                self._lsp_available = True
            except ImportError:
                logger.warning("multilspy not installed, using fallback mode")
                self._lsp_available = False
                self._initialized = True
                return True

            # Detect languages in project
            languages = self._detect_languages()

            if not languages:
                logger.info("No supported languages detected")
                self._initialized = True
                return True

            # Initialize servers for each language
            for lang in languages:
                try:
                    server = LanguageServer.create(
                        config={"language": lang},
                        repository_root_path=str(self.project_path),
                    )
                    self._servers[lang] = server
                    logger.info(f"Started LSP server for {lang}")
                except Exception as e:
                    logger.warning(f"Failed to start {lang} server: {e}")

            self._initialized = True
            return True

        except Exception as e:
            logger.error(f"LSP initialization failed: {e}")
            self._initialized = True
            self._lsp_available = False
            return False

    def _detect_languages(self) -> List[str]:
        """Detect programming languages in the project."""
        languages = set()

        # Check src/ directory (CFA v2)
        src_dir = self.project_path / "src"
        if not src_dir.exists():
            src_dir = self.project_path

        for file_path in src_dir.rglob("*"):
            if file_path.is_file():
                ext = file_path.suffix.lower()
                if ext in LANGUAGE_SERVERS:
                    languages.add(LANGUAGE_SERVERS[ext])

        return list(languages)

    def restart(self, language: Optional[str] = None) -> Dict[str, Any]:
        """
        Restart LSP server(s).

        Args:
            language: Specific language to restart, or None for all

        Returns:
            Status of restart operation
        """
        if not self._lsp_available:
            return {"success": True, "message": "LSP not available, nothing to restart"}

        restarted = []
        failed = []

        servers_to_restart = (
            [language] if language else list(self._servers.keys())
        )

        for lang in servers_to_restart:
            if lang in self._servers:
                try:
                    # Shutdown old server
                    old_server = self._servers.pop(lang)
                    old_server.shutdown()

                    # Start new server
                    from multilspy import LanguageServer
                    new_server = LanguageServer.create(
                        config={"language": lang},
                        repository_root_path=str(self.project_path),
                    )
                    self._servers[lang] = new_server
                    restarted.append(lang)
                except Exception as e:
                    failed.append({"language": lang, "error": str(e)})

        return {
            "success": len(failed) == 0,
            "restarted": restarted,
            "failed": failed,
        }

    def get_server(self, file_path: Path) -> Optional[Any]:
        """Get the appropriate LSP server for a file."""
        if not self._lsp_available:
            return None

        ext = file_path.suffix.lower()
        lang = LANGUAGE_SERVERS.get(ext)

        if lang and lang in self._servers:
            return self._servers[lang]

        return None

    def shutdown(self):
        """Shutdown all LSP servers."""
        for lang, server in self._servers.items():
            try:
                server.shutdown()
                logger.info(f"Shutdown {lang} server")
            except Exception as e:
                logger.warning(f"Error shutting down {lang} server: {e}")

        self._servers.clear()
        self._initialized = False

    def get_status(self) -> Dict[str, Any]:
        """Get status of all LSP servers."""
        return {
            "initialized": self._initialized,
            "lsp_available": getattr(self, "_lsp_available", False),
            "project_path": str(self.project_path),
            "active_servers": list(self._servers.keys()),
            "supported_extensions": list(LANGUAGE_SERVERS.keys()),
        }


# Global manager cache
_managers: Dict[str, LSPManager] = {}


def get_lsp_manager(project_path: str) -> LSPManager:
    """
    Get or create an LSP manager for a project.

    Managers are cached per project path.
    """
    path = str(Path(project_path).resolve())

    if path not in _managers:
        manager = LSPManager(project_path=path)
        manager.initialize()
        _managers[path] = manager

    return _managers[path]


def shutdown_all_managers():
    """Shutdown all cached LSP managers."""
    for manager in _managers.values():
        manager.shutdown()
    _managers.clear()
