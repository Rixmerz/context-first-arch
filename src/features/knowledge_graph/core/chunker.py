"""
Code Chunker for Project Knowledge Graph.

Converts source files into knowledge chunks using language analyzers.
Extracts: SOURCE_FILE, FUNCTION, CLASS, TEST, CONFIG, METADATA chunks.
"""

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from src.core.analyzers import get_registry
from src.core.analyzers.base import FileAnalysis, FunctionInfo, ClassInfo
from .models import ChunkType, KnowledgeChunk


# Approximate tokens per character (for estimation without tiktoken)
TOKENS_PER_CHAR = 0.25

# File patterns for special chunk types
CONFIG_PATTERNS = [
    ".env", ".env.*", "*.config.js", "*.config.ts", "*.config.mjs",
    "config.py", "settings.py", "config/*.py", "config/*.json",
    "*.yaml", "*.yml", "*.toml", "*.ini",
]

METADATA_PATTERNS = [
    "package.json", "pyproject.toml", "Cargo.toml", "go.mod",
    "requirements.txt", "setup.py", "setup.cfg", "pom.xml",
    "build.gradle", "Gemfile", "composer.json",
]

TEST_PATTERNS = [
    "test_*.py", "*_test.py", "tests/*.py",
    "*.test.ts", "*.test.js", "*.spec.ts", "*.spec.js",
    "__tests__/*", "test/*", "tests/*",
]

# Directories to skip
SKIP_DIRS = {
    "node_modules", ".git", "__pycache__", ".venv", "venv",
    ".tox", ".pytest_cache", ".mypy_cache", "dist", "build",
    ".next", ".nuxt", "coverage", ".coverage",
}

# Binary/non-text extensions to skip
SKIP_EXTENSIONS = {
    ".pyc", ".pyo", ".so", ".dll", ".exe", ".bin",
    ".png", ".jpg", ".jpeg", ".gif", ".ico", ".svg",
    ".woff", ".woff2", ".ttf", ".eot",
    ".pdf", ".doc", ".docx", ".xls", ".xlsx",
    ".zip", ".tar", ".gz", ".rar",
    ".mp3", ".mp4", ".avi", ".mov",
    ".db", ".sqlite", ".sqlite3",
}


def estimate_tokens(text: str) -> int:
    """
    Estimate token count without tiktoken.

    Uses character-based estimation (roughly 4 chars per token for code).
    For more accurate counts, install tiktoken.
    """
    try:
        import tiktoken
        enc = tiktoken.get_encoding("cl100k_base")
        return len(enc.encode(text))
    except ImportError:
        # Fallback to estimation
        return int(len(text) * TOKENS_PER_CHAR)


def infer_feature(file_path: str, project_path: Path) -> Optional[str]:
    """
    Infer feature name from file path following CFA conventions.

    CFA v2 structure:
    - src/features/auth/... -> "auth"
    - src/core/... -> "core"
    - impl/user.ts -> "user"
    - contracts/auth.contract.md -> "auth"
    """
    try:
        rel_path = Path(file_path).relative_to(project_path)
        parts = rel_path.parts

        if len(parts) < 2:
            return None

        # src/features/X/... -> X
        if parts[0] == "src" and len(parts) >= 3:
            if parts[1] == "features":
                return parts[2]
            elif parts[1] in ("core", "shared", "utils"):
                return parts[1]

        # impl/X.ts or impl/X/... -> X
        if parts[0] == "impl":
            if len(parts) == 2:
                return Path(parts[1]).stem
            else:
                return parts[1]

        # contracts/X.contract.md -> X
        if parts[0] == "contracts":
            name = Path(parts[1]).stem
            return name.replace(".contract", "")

        return None
    except ValueError:
        return None


class CodeChunker:
    """
    Extracts code chunks from source files.

    Uses language analyzers to extract functions, classes, and imports.
    Also handles special file types (config, metadata, tests).
    """

    def __init__(self, project_path: Path):
        """
        Initialize code chunker.

        Args:
            project_path: Root path of the project
        """
        self.project_path = project_path
        self.registry = get_registry()

    def chunk_file(self, file_path: Path) -> List[KnowledgeChunk]:
        """
        Extract all chunks from a single file.

        Args:
            file_path: Path to the source file

        Returns:
            List of KnowledgeChunk objects
        """
        chunks: List[KnowledgeChunk] = []

        # Get relative path for IDs
        try:
            rel_path = str(file_path.relative_to(self.project_path))
        except ValueError:
            rel_path = str(file_path)

        # Read file content
        try:
            content = file_path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, IOError):
            return chunks

        # Determine chunk type based on file patterns
        chunk_type = self._determine_chunk_type(file_path, rel_path)
        feature = infer_feature(str(file_path), self.project_path)

        # Create SOURCE_FILE chunk (always)
        source_chunk = self._create_source_file_chunk(
            file_path, rel_path, content, chunk_type, feature
        )
        chunks.append(source_chunk)

        # For code files, also extract function/class chunks
        if chunk_type == ChunkType.SOURCE_FILE:
            analyzer = self.registry.get_analyzer_for_file(file_path)
            if analyzer:
                try:
                    analysis = analyzer.analyze_file(file_path)
                    function_chunks = self._extract_function_chunks(
                        file_path, rel_path, content, analysis, feature
                    )
                    chunks.extend(function_chunks)

                    # Extract class chunks
                    class_chunks = self._extract_class_chunks(
                        file_path, rel_path, content, analysis, feature
                    )
                    chunks.extend(class_chunks)
                except Exception:
                    # Analysis failed, but we still have the source file chunk
                    pass

        return chunks

    def chunk_directory(
        self,
        directory: Optional[Path] = None,
        include_types: Optional[Set[ChunkType]] = None,
        exclude_patterns: Optional[List[str]] = None
    ) -> List[KnowledgeChunk]:
        """
        Extract chunks from all files in a directory.

        Args:
            directory: Directory to scan (defaults to project root)
            include_types: Only include these chunk types
            exclude_patterns: Glob patterns to exclude

        Returns:
            List of all extracted chunks
        """
        directory = directory or self.project_path
        all_chunks: List[KnowledgeChunk] = []
        exclude_patterns = exclude_patterns or []

        for file_path in self._iter_source_files(directory):
            # Check exclusion patterns
            rel_path = str(file_path.relative_to(self.project_path))
            if any(self._match_pattern(rel_path, p) for p in exclude_patterns):
                continue

            chunks = self.chunk_file(file_path)

            # Filter by type if specified
            if include_types:
                chunks = [c for c in chunks if c.chunk_type in include_types]

            all_chunks.extend(chunks)

        return all_chunks

    def _iter_source_files(self, directory: Path):
        """Iterate over source files, skipping non-text and ignored directories."""
        for item in directory.iterdir():
            if item.is_dir():
                if item.name not in SKIP_DIRS and not item.name.startswith("."):
                    yield from self._iter_source_files(item)
            elif item.is_file():
                if item.suffix.lower() not in SKIP_EXTENSIONS:
                    yield item

    def _determine_chunk_type(self, file_path: Path, rel_path: str) -> ChunkType:
        """Determine the appropriate chunk type for a file."""
        file_name = file_path.name.lower()

        # Check metadata patterns
        for pattern in METADATA_PATTERNS:
            if self._match_pattern(file_name, pattern):
                return ChunkType.METADATA

        # Check config patterns
        for pattern in CONFIG_PATTERNS:
            if self._match_pattern(rel_path, pattern) or self._match_pattern(file_name, pattern):
                return ChunkType.CONFIG

        # Check test patterns
        for pattern in TEST_PATTERNS:
            if self._match_pattern(rel_path, pattern) or self._match_pattern(file_name, pattern):
                return ChunkType.TEST

        # Default to source file
        return ChunkType.SOURCE_FILE

    def _match_pattern(self, path: str, pattern: str) -> bool:
        """Simple glob-like pattern matching."""
        import fnmatch
        return fnmatch.fnmatch(path, pattern) or fnmatch.fnmatch(Path(path).name, pattern)

    def _create_source_file_chunk(
        self,
        file_path: Path,
        rel_path: str,
        content: str,
        chunk_type: ChunkType,
        feature: Optional[str]
    ) -> KnowledgeChunk:
        """Create a SOURCE_FILE chunk."""
        # Count lines
        lines = content.split("\n")
        line_count = len(lines)

        # Generate compressed version (first 50 lines + "...")
        if line_count > 50:
            compressed = "\n".join(lines[:50]) + "\n# ... (truncated)"
        else:
            compressed = content

        # Estimate tokens
        token_count = estimate_tokens(content)
        token_count_compressed = estimate_tokens(compressed)

        # Determine tags
        tags = []
        if chunk_type == ChunkType.TEST:
            tags.append("test")
        elif chunk_type == ChunkType.CONFIG:
            tags.append("config")
        elif chunk_type == ChunkType.METADATA:
            tags.append("metadata")

        # Add language tag
        analyzer = self.registry.get_analyzer_for_file(file_path)
        if analyzer:
            tags.append(analyzer.language)

        return KnowledgeChunk(
            id=f"{rel_path}",
            chunk_type=chunk_type,
            content=content,
            content_compressed=compressed,
            token_count=token_count,
            token_count_compressed=token_count_compressed,
            file_path=rel_path,
            line_start=1,
            line_end=line_count,
            feature=feature,
            tags=tags,
        )

    def _extract_function_chunks(
        self,
        file_path: Path,
        rel_path: str,
        content: str,
        analysis: FileAnalysis,
        feature: Optional[str]
    ) -> List[KnowledgeChunk]:
        """Extract FUNCTION chunks from file analysis."""
        chunks: List[KnowledgeChunk] = []
        lines = content.split("\n")

        for func in analysis.functions:
            # Extract function content
            func_lines = lines[func.start_line - 1:func.end_line]
            func_content = "\n".join(func_lines)

            # Create signature-only compressed version
            compressed = func.signature
            if func.docstring:
                compressed += f'\n    """{func.docstring}"""'
            compressed += "\n    ..."

            # Estimate tokens
            token_count = estimate_tokens(func_content)
            token_count_compressed = estimate_tokens(compressed)

            # Build chunk ID
            chunk_id = f"{rel_path}:{func.name}"

            # Tags
            tags = ["function"]
            if func.is_async:
                tags.append("async")
            if func.is_exported:
                tags.append("exported")

            chunks.append(KnowledgeChunk(
                id=chunk_id,
                chunk_type=ChunkType.FUNCTION,
                content=func_content,
                content_compressed=compressed,
                token_count=token_count,
                token_count_compressed=token_count_compressed,
                file_path=rel_path,
                line_start=func.start_line,
                line_end=func.end_line,
                symbol_name=func.name,
                signature=func.signature,
                docstring=func.docstring,
                feature=feature,
                tags=tags,
                extra={
                    "is_async": func.is_async,
                    "is_exported": func.is_exported,
                    "calls": func.calls,
                    "parameters": func.parameters,
                    "return_type": func.return_type,
                }
            ))

        return chunks

    def _extract_class_chunks(
        self,
        file_path: Path,
        rel_path: str,
        content: str,
        analysis: FileAnalysis,
        feature: Optional[str]
    ) -> List[KnowledgeChunk]:
        """Extract CLASS chunks from file analysis."""
        chunks: List[KnowledgeChunk] = []
        lines = content.split("\n")

        for cls in analysis.classes:
            # Extract class content
            cls_lines = lines[cls.start_line - 1:cls.end_line]
            cls_content = "\n".join(cls_lines)

            # Create signature-only compressed version
            compressed = cls.signature
            if cls.docstring:
                compressed += f'\n    """{cls.docstring}"""'
            if cls.methods:
                method_list = ", ".join(cls.methods[:10])
                if len(cls.methods) > 10:
                    method_list += f", ... (+{len(cls.methods) - 10} more)"
                compressed += f"\n    # Methods: {method_list}"
            compressed += "\n    ..."

            # Estimate tokens
            token_count = estimate_tokens(cls_content)
            token_count_compressed = estimate_tokens(compressed)

            # Build chunk ID
            chunk_id = f"{rel_path}:class:{cls.name}"

            # Tags
            tags = ["class"]
            if cls.is_exported:
                tags.append("exported")
            if cls.base_classes:
                tags.append("extends")
            if cls.decorators:
                tags.extend([f"@{d.split('(')[0]}" for d in cls.decorators[:3]])

            chunks.append(KnowledgeChunk(
                id=chunk_id,
                chunk_type=ChunkType.CLASS,
                content=cls_content,
                content_compressed=compressed,
                token_count=token_count,
                token_count_compressed=token_count_compressed,
                file_path=rel_path,
                line_start=cls.start_line,
                line_end=cls.end_line,
                symbol_name=cls.name,
                signature=cls.signature,
                docstring=cls.docstring,
                feature=feature,
                tags=tags,
                extra={
                    "base_classes": cls.base_classes,
                    "methods": cls.methods,
                    "is_exported": cls.is_exported,
                    "decorators": cls.decorators,
                }
            ))

        return chunks


class ContractChunker:
    """
    Extracts CONTRACT chunks from CFA contract files.
    """

    def __init__(self, project_path: Path):
        self.project_path = project_path

    def chunk_contracts(self) -> List[KnowledgeChunk]:
        """Extract chunks from all contract files."""
        contracts_dir = self.project_path / "contracts"
        if not contracts_dir.exists():
            return []

        chunks: List[KnowledgeChunk] = []

        for contract_file in contracts_dir.glob("*.contract.md"):
            chunk = self._chunk_contract(contract_file)
            if chunk:
                chunks.append(chunk)

        return chunks

    def _chunk_contract(self, file_path: Path) -> Optional[KnowledgeChunk]:
        """Create CONTRACT chunk from a contract file."""
        try:
            content = file_path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, IOError):
            return None

        rel_path = str(file_path.relative_to(self.project_path))
        feature = file_path.stem.replace(".contract", "")

        # Parse contract header for signature
        signature = self._extract_contract_signature(content)

        return KnowledgeChunk(
            id=f"contract:{feature}",
            chunk_type=ChunkType.CONTRACT,
            content=content,
            content_compressed=signature,
            token_count=estimate_tokens(content),
            token_count_compressed=estimate_tokens(signature),
            file_path=rel_path,
            line_start=1,
            line_end=len(content.split("\n")),
            symbol_name=feature,
            signature=signature,
            feature=feature,
            tags=["contract", "interface"],
        )

    def _extract_contract_signature(self, content: str) -> str:
        """Extract the interface signature from a contract."""
        lines = content.split("\n")
        signature_lines = []

        in_interface = False
        for line in lines:
            if line.startswith("# ") or line.startswith("## Interface"):
                in_interface = True
                signature_lines.append(line)
            elif in_interface:
                if line.startswith("## ") and "Interface" not in line:
                    break
                if line.startswith("- ") or line.startswith("```"):
                    signature_lines.append(line)

        if signature_lines:
            return "\n".join(signature_lines[:20])

        # Fallback: first 10 lines
        return "\n".join(lines[:10])


class ConfigChunker:
    """
    Extracts CONFIG and METADATA chunks from config files.
    """

    def __init__(self, project_path: Path):
        self.project_path = project_path

    def chunk_configs(self) -> List[KnowledgeChunk]:
        """Extract chunks from config and metadata files."""
        chunks: List[KnowledgeChunk] = []

        # Find config files
        for pattern in CONFIG_PATTERNS + METADATA_PATTERNS:
            for file_path in self.project_path.glob(pattern):
                if file_path.is_file():
                    chunk = self._chunk_config(file_path)
                    if chunk:
                        chunks.append(chunk)

        return chunks

    def _chunk_config(self, file_path: Path) -> Optional[KnowledgeChunk]:
        """Create CONFIG or METADATA chunk."""
        try:
            content = file_path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, IOError):
            return None

        rel_path = str(file_path.relative_to(self.project_path))

        # Determine type
        chunk_type = ChunkType.METADATA
        for pattern in CONFIG_PATTERNS:
            if any(file_path.match(p) for p in [pattern]):
                chunk_type = ChunkType.CONFIG
                break

        # Extract key info for compressed version
        compressed = self._extract_config_summary(content, file_path)

        return KnowledgeChunk(
            id=f"config:{rel_path}",
            chunk_type=chunk_type,
            content=content,
            content_compressed=compressed,
            token_count=estimate_tokens(content),
            token_count_compressed=estimate_tokens(compressed),
            file_path=rel_path,
            line_start=1,
            line_end=len(content.split("\n")),
            symbol_name=file_path.name,
            tags=["config" if chunk_type == ChunkType.CONFIG else "metadata"],
        )

    def _extract_config_summary(self, content: str, file_path: Path) -> str:
        """Extract key information from config file."""
        ext = file_path.suffix.lower()

        if ext == ".json":
            try:
                data = json.loads(content)
                if isinstance(data, dict):
                    # For package.json, extract key fields
                    if file_path.name == "package.json":
                        summary = {
                            "name": data.get("name"),
                            "version": data.get("version"),
                            "dependencies": list(data.get("dependencies", {}).keys())[:10],
                            "devDependencies": list(data.get("devDependencies", {}).keys())[:10],
                        }
                        return json.dumps(summary, indent=2)
                    # Generic: just keys
                    return f"Keys: {list(data.keys())}"
            except json.JSONDecodeError:
                pass

        # Fallback: first 20 lines
        lines = content.split("\n")
        return "\n".join(lines[:20])


def chunk_project(
    project_path: Path,
    include_types: Optional[Set[ChunkType]] = None
) -> List[KnowledgeChunk]:
    """
    Convenience function to chunk an entire project.

    Args:
        project_path: Root path of the project
        include_types: Only include these chunk types

    Returns:
        List of all extracted chunks
    """
    all_chunks: List[KnowledgeChunk] = []

    # Code chunks
    code_chunker = CodeChunker(project_path)
    all_chunks.extend(code_chunker.chunk_directory(include_types=include_types))

    # Contract chunks
    if not include_types or ChunkType.CONTRACT in include_types:
        contract_chunker = ContractChunker(project_path)
        all_chunks.extend(contract_chunker.chunk_contracts())

    return all_chunks
