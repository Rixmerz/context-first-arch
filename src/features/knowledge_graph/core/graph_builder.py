"""
Graph Builder for Project Knowledge Graph.

Builds edges between chunks based on code relationships:
- CALLS: Function A calls Function B
- IMPORTS: File A imports from File B
- CONTAINS: Class contains Method
- TESTED_BY: Code is tested by Test
- IMPLEMENTS: Code implements Contract
"""

import re
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from .models import (
    ChunkEdge,
    ChunkType,
    EdgeType,
    KnowledgeChunk,
)
from .storage import ChunkStorage
from .chunker import CodeChunker, ContractChunker, chunk_project


class GraphBuilder:
    """
    Builds the Knowledge Graph by creating edges between chunks.

    Edge types created:
    - CALLS: From function calls analysis
    - IMPORTS: From import statements
    - CONTAINS: File → Functions within it
    - TESTED_BY: Code → Test files that test it
    - IMPLEMENTS: Code → Contracts it implements
    """

    def __init__(self, project_path: Path, storage: ChunkStorage):
        """
        Initialize graph builder.

        Args:
            project_path: Root path of the project
            storage: ChunkStorage instance for persistence
        """
        self.project_path = project_path
        self.storage = storage

    def build_graph(
        self,
        incremental: bool = False,
        changed_files: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Build or update the Knowledge Graph.

        Args:
            incremental: If True, only update changed files
            changed_files: List of changed file paths (for incremental)

        Returns:
            Build statistics
        """
        start_time = datetime.now()

        if incremental and changed_files:
            stats = self._incremental_build(changed_files)
        else:
            stats = self._full_build()

        # Mark build complete
        self.storage.mark_build_complete()

        stats["build_time_ms"] = int((datetime.now() - start_time).total_seconds() * 1000)
        return stats

    def _full_build(self) -> Dict[str, Any]:
        """Perform full graph rebuild."""
        # Clear existing data
        self.storage.clear_all()

        # Extract all chunks
        chunks = chunk_project(self.project_path)

        # Save chunks
        self.storage.save_chunks(chunks)

        # Build edges
        edges = self._build_all_edges(chunks)
        self.storage.save_edges(edges)

        return {
            "mode": "full",
            "chunks_created": len(chunks),
            "edges_created": len(edges),
            "chunks_by_type": self._count_by_type(chunks),
            "edges_by_type": self._count_edges_by_type(edges),
        }

    def _incremental_build(self, changed_files: List[str]) -> Dict[str, Any]:
        """Perform incremental update for changed files."""
        chunks_updated = 0
        edges_updated = 0

        code_chunker = CodeChunker(self.project_path)

        for rel_path in changed_files:
            file_path = self.project_path / rel_path

            if not file_path.exists():
                # File was deleted - remove its chunks
                self.storage.delete_chunks_by_file(rel_path)
                continue

            # Delete old chunks for this file
            self.storage.delete_chunks_by_file(rel_path)

            # Extract new chunks
            chunks = code_chunker.chunk_file(file_path)
            self.storage.save_chunks(chunks)
            chunks_updated += len(chunks)

            # Rebuild edges for these chunks
            all_chunks = self.storage.get_chunks([c.id for c in chunks])
            # Also get all chunks for edge building context
            all_project_chunks = [
                self.storage.get_chunk(cid)
                for cid in self.storage.get_all_chunk_ids()
            ]
            all_project_chunks = [c for c in all_project_chunks if c]

            edges = self._build_edges_for_chunks(chunks, all_project_chunks)
            self.storage.save_edges(edges)
            edges_updated += len(edges)

        return {
            "mode": "incremental",
            "files_updated": len(changed_files),
            "chunks_updated": chunks_updated,
            "edges_updated": edges_updated,
        }

    def _build_all_edges(self, chunks: List[KnowledgeChunk]) -> List[ChunkEdge]:
        """Build all edges between chunks."""
        edges: List[ChunkEdge] = []

        # Index chunks by various keys for fast lookup
        chunks_by_id = {c.id: c for c in chunks}
        chunks_by_file = defaultdict(list)
        chunks_by_symbol = defaultdict(list)
        functions_by_name = defaultdict(list)
        classes_by_name = defaultdict(list)

        for chunk in chunks:
            if chunk.file_path:
                chunks_by_file[chunk.file_path].append(chunk)
            if chunk.symbol_name:
                chunks_by_symbol[chunk.symbol_name].append(chunk)
                if chunk.chunk_type == ChunkType.FUNCTION:
                    functions_by_name[chunk.symbol_name].append(chunk)
                elif chunk.chunk_type == ChunkType.CLASS:
                    classes_by_name[chunk.symbol_name].append(chunk)

        # 1. CONTAINS edges (file → functions/classes, class → methods)
        edges.extend(self._build_contains_edges(chunks_by_file))

        # 2. CALLS edges (function → function)
        edges.extend(self._build_calls_edges(chunks, functions_by_name))

        # 3. IMPORTS edges (file → file)
        edges.extend(self._build_imports_edges(chunks, chunks_by_file))

        # 4. TESTED_BY edges (code → test)
        edges.extend(self._build_tested_by_edges(chunks, chunks_by_file))

        # 5. IMPLEMENTS edges (code → contract)
        edges.extend(self._build_implements_edges(chunks))

        # 6. INHERITS edges (class → base class)
        edges.extend(self._build_inherits_edges(chunks, classes_by_name))

        return edges

    def _build_edges_for_chunks(
        self,
        target_chunks: List[KnowledgeChunk],
        all_chunks: List[KnowledgeChunk]
    ) -> List[ChunkEdge]:
        """Build edges for specific chunks."""
        # Use full edge building logic but filter to target chunks
        all_edges = self._build_all_edges(all_chunks)

        target_ids = {c.id for c in target_chunks}
        return [
            e for e in all_edges
            if e.source_id in target_ids or e.target_id in target_ids
        ]

    def _build_contains_edges(
        self,
        chunks_by_file: Dict[str, List[KnowledgeChunk]]
    ) -> List[ChunkEdge]:
        """Build CONTAINS edges from files to functions/classes, and classes to methods."""
        edges: List[ChunkEdge] = []

        for file_path, file_chunks in chunks_by_file.items():
            # Find the source file chunk
            source_file = None
            functions = []
            classes = []

            for chunk in file_chunks:
                if chunk.chunk_type == ChunkType.SOURCE_FILE:
                    source_file = chunk
                elif chunk.chunk_type == ChunkType.FUNCTION:
                    functions.append(chunk)
                elif chunk.chunk_type == ChunkType.CLASS:
                    classes.append(chunk)

            # File → Functions (top-level functions only)
            if source_file and functions:
                for func in functions:
                    # Check if function is a method (inside a class)
                    is_method = any(
                        cls.line_start <= func.line_start <= cls.line_end
                        for cls in classes
                    )
                    if not is_method:
                        edges.append(ChunkEdge(
                            source_id=source_file.id,
                            target_id=func.id,
                            edge_type=EdgeType.CONTAINS,
                            weight=1.0,
                            metadata={"line": func.line_start}
                        ))

            # File → Classes
            if source_file and classes:
                for cls in classes:
                    edges.append(ChunkEdge(
                        source_id=source_file.id,
                        target_id=cls.id,
                        edge_type=EdgeType.CONTAINS,
                        weight=1.0,
                        metadata={"line": cls.line_start}
                    ))

            # Class → Methods
            for cls in classes:
                cls_methods = cls.extra.get("methods", [])
                for func in functions:
                    # Check if function is within class boundaries
                    if cls.line_start <= func.line_start <= cls.line_end:
                        edges.append(ChunkEdge(
                            source_id=cls.id,
                            target_id=func.id,
                            edge_type=EdgeType.CONTAINS,
                            weight=1.0,
                            metadata={
                                "line": func.line_start,
                                "relationship": "method"
                            }
                        ))

        return edges

    def _build_calls_edges(
        self,
        chunks: List[KnowledgeChunk],
        functions_by_name: Dict[str, List[KnowledgeChunk]]
    ) -> List[ChunkEdge]:
        """Build CALLS edges between functions."""
        edges: List[ChunkEdge] = []

        for chunk in chunks:
            if chunk.chunk_type != ChunkType.FUNCTION:
                continue

            # Get called functions from extra data
            calls = chunk.extra.get("calls", [])

            for called_name in calls:
                # Find target function chunks
                if called_name in functions_by_name:
                    for target in functions_by_name[called_name]:
                        # Avoid self-references
                        if target.id != chunk.id:
                            edges.append(ChunkEdge(
                                source_id=chunk.id,
                                target_id=target.id,
                                edge_type=EdgeType.CALLS,
                                weight=1.0,
                            ))

        return edges

    def _build_imports_edges(
        self,
        chunks: List[KnowledgeChunk],
        chunks_by_file: Dict[str, List[KnowledgeChunk]]
    ) -> List[ChunkEdge]:
        """Build IMPORTS edges between files."""
        edges: List[ChunkEdge] = []

        # This requires import information which should be in chunk extra data
        # For now, we'll parse simple import patterns from source files

        for chunk in chunks:
            if chunk.chunk_type not in (ChunkType.SOURCE_FILE, ChunkType.TEST):
                continue

            # Extract imports from content
            imports = self._extract_imports(chunk.content, chunk.file_path or "")

            for imported_path in imports:
                # Normalize path
                normalized = self._normalize_import_path(imported_path, chunk.file_path or "")

                # Find target file chunk
                if normalized in chunks_by_file:
                    target_chunks = [
                        c for c in chunks_by_file[normalized]
                        if c.chunk_type == ChunkType.SOURCE_FILE
                    ]
                    if target_chunks:
                        edges.append(ChunkEdge(
                            source_id=chunk.id,
                            target_id=target_chunks[0].id,
                            edge_type=EdgeType.IMPORTS,
                            weight=1.0,
                            metadata={"imported": imported_path}
                        ))

        return edges

    def _build_tested_by_edges(
        self,
        chunks: List[KnowledgeChunk],
        chunks_by_file: Dict[str, List[KnowledgeChunk]]
    ) -> List[ChunkEdge]:
        """Build TESTED_BY edges from code to tests."""
        edges: List[ChunkEdge] = []

        # Find test chunks
        test_chunks = [c for c in chunks if c.chunk_type == ChunkType.TEST]

        for test_chunk in test_chunks:
            # Try to find what this test tests
            # Strategy 1: Test file naming convention
            tested_file = self._infer_tested_file(test_chunk.file_path or "")

            if tested_file and tested_file in chunks_by_file:
                source_chunks = chunks_by_file[tested_file]
                for source in source_chunks:
                    edges.append(ChunkEdge(
                        source_id=source.id,
                        target_id=test_chunk.id,
                        edge_type=EdgeType.TESTED_BY,
                        weight=1.0,
                    ))

            # Strategy 2: Look for imports in test file
            if test_chunk.content:
                imports = self._extract_imports(test_chunk.content, test_chunk.file_path or "")
                for imported in imports:
                    normalized = self._normalize_import_path(imported, test_chunk.file_path or "")
                    if normalized in chunks_by_file:
                        for source in chunks_by_file[normalized]:
                            if source.chunk_type != ChunkType.TEST:
                                edges.append(ChunkEdge(
                                    source_id=source.id,
                                    target_id=test_chunk.id,
                                    edge_type=EdgeType.TESTED_BY,
                                    weight=0.8,  # Lower weight for import-inferred
                                ))

        return edges

    def _build_implements_edges(
        self,
        chunks: List[KnowledgeChunk]
    ) -> List[ChunkEdge]:
        """Build IMPLEMENTS edges from code to contracts."""
        edges: List[ChunkEdge] = []

        # Find contract chunks
        contracts = [c for c in chunks if c.chunk_type == ChunkType.CONTRACT]

        # Find code chunks by feature
        code_by_feature: Dict[str, List[KnowledgeChunk]] = defaultdict(list)
        for chunk in chunks:
            if chunk.feature and chunk.chunk_type in (ChunkType.SOURCE_FILE, ChunkType.FUNCTION):
                code_by_feature[chunk.feature].append(chunk)

        for contract in contracts:
            feature = contract.feature or contract.symbol_name
            if feature and feature in code_by_feature:
                for code_chunk in code_by_feature[feature]:
                    edges.append(ChunkEdge(
                        source_id=code_chunk.id,
                        target_id=contract.id,
                        edge_type=EdgeType.IMPLEMENTS,
                        weight=1.0,
                    ))

        return edges

    def _build_inherits_edges(
        self,
        chunks: List[KnowledgeChunk],
        classes_by_name: Dict[str, List[KnowledgeChunk]]
    ) -> List[ChunkEdge]:
        """Build INHERITS edges between classes."""
        edges: List[ChunkEdge] = []

        for chunk in chunks:
            if chunk.chunk_type != ChunkType.CLASS:
                continue

            # Get base classes from extra data
            base_classes = chunk.extra.get("base_classes", [])

            for base_name in base_classes:
                # Simple name extraction (handles Module.ClassName)
                simple_name = base_name.split(".")[-1]

                # Find target class chunks
                if simple_name in classes_by_name:
                    for target in classes_by_name[simple_name]:
                        # Avoid self-references
                        if target.id != chunk.id:
                            edges.append(ChunkEdge(
                                source_id=chunk.id,
                                target_id=target.id,
                                edge_type=EdgeType.INHERITS,
                                weight=1.0,
                                metadata={"base_class": base_name}
                            ))

        return edges

    def _extract_imports(self, content: str, file_path: str) -> List[str]:
        """Extract import paths from file content."""
        imports: List[str] = []

        # Python imports
        python_patterns = [
            r'from\s+([\w.]+)\s+import',
            r'import\s+([\w.]+)',
        ]

        # JavaScript/TypeScript imports
        js_patterns = [
            r'import\s+.*?from\s+[\'"]([^"\']+)[\'"]',
            r'require\([\'"]([^"\']+)[\'"]\)',
        ]

        # Rust imports
        rust_patterns = [
            r'use\s+([\w:]+)',
            r'mod\s+(\w+)',
        ]

        patterns = python_patterns + js_patterns + rust_patterns

        for pattern in patterns:
            matches = re.findall(pattern, content)
            imports.extend(matches)

        return imports

    def _normalize_import_path(self, import_path: str, source_file: str) -> str:
        """Normalize import path to relative file path."""
        # Handle relative imports
        if import_path.startswith("."):
            source_dir = str(Path(source_file).parent)
            # Simple resolution
            parts = import_path.split(".")
            if parts[0] == "":
                # from . import x or from .module import x
                resolved = source_dir
            else:
                resolved = str(Path(source_dir) / "/".join(parts[1:]))
            return resolved

        # Handle Python-style module imports
        if "." in import_path and not import_path.startswith("/"):
            # Convert module.submodule to module/submodule
            return import_path.replace(".", "/")

        return import_path

    def _infer_tested_file(self, test_file_path: str) -> Optional[str]:
        """Infer the source file being tested from test file path."""
        test_path = Path(test_file_path)
        test_name = test_path.name

        # Common patterns:
        # test_foo.py -> foo.py
        # foo_test.py -> foo.py
        # foo.test.ts -> foo.ts
        # foo.spec.js -> foo.js
        # __tests__/foo.ts -> ../foo.ts

        patterns = [
            (r'^test_(.+)\.py$', r'\1.py'),
            (r'^(.+)_test\.py$', r'\1.py'),
            (r'^(.+)\.test\.(ts|js|tsx|jsx)$', r'\1.\2'),
            (r'^(.+)\.spec\.(ts|js|tsx|jsx)$', r'\1.\2'),
        ]

        for pattern, replacement in patterns:
            match = re.match(pattern, test_name)
            if match:
                source_name = re.sub(pattern, replacement, test_name)

                # Try to find in same directory first
                same_dir = test_path.parent / source_name
                if "__tests__" in str(test_path):
                    # Look in parent directory
                    parent_dir = test_path.parent.parent / source_name
                    return str(parent_dir)

                return str(same_dir)

        return None

    def _count_by_type(self, chunks: List[KnowledgeChunk]) -> Dict[str, int]:
        """Count chunks by type."""
        counts: Dict[str, int] = {}
        for chunk in chunks:
            type_name = chunk.chunk_type.value
            counts[type_name] = counts.get(type_name, 0) + 1
        return counts

    def _count_edges_by_type(self, edges: List[ChunkEdge]) -> Dict[str, int]:
        """Count edges by type."""
        counts: Dict[str, int] = {}
        for edge in edges:
            type_name = edge.edge_type.value
            counts[type_name] = counts.get(type_name, 0) + 1
        return counts


async def build_knowledge_graph(
    project_path: str,
    incremental: bool = False,
    changed_files: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Build or update the Knowledge Graph for a project.

    Args:
        project_path: Path to the project
        incremental: If True, only update changed files
        changed_files: List of changed file paths

    Returns:
        Build statistics
    """
    path = Path(project_path)
    storage = ChunkStorage(path)
    builder = GraphBuilder(path, storage)

    return builder.build_graph(
        incremental=incremental,
        changed_files=changed_files
    )
