"""
Intelligent Context Retriever for Project Knowledge Graph.

Retrieves task-relevant context using:
- BM25 text search for initial matching
- Multi-hop graph traversal for related context
- Omission transparency (CRITICAL)
- Progressive disclosure / compression
"""

import re
import time
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from .models import (
    ChunkEdge,
    ChunkType,
    CompressionLevel,
    ContextBundle,
    EdgeType,
    ExpansionOption,
    KnowledgeChunk,
    OmissionReason,
    OmittedChunk,
)
from .storage import ChunkStorage


# Try to import rank_bm25 for better search
try:
    from rank_bm25 import BM25Okapi
    HAS_BM25 = True
except ImportError:
    HAS_BM25 = False


# Priority weights for chunk types (higher = more important)
CHUNK_TYPE_PRIORITY = {
    ChunkType.CONTRACT: 10,
    ChunkType.FUNCTION: 9,
    ChunkType.CLASS: 9,
    ChunkType.TEST: 8,
    ChunkType.CONFIG: 7,
    ChunkType.METADATA: 6,
    ChunkType.SOURCE_FILE: 5,
    ChunkType.BUSINESS_RULE: 10,
    ChunkType.COMMIT: 3,
    ChunkType.AST: 2,
    ChunkType.CALLGRAPH: 2,
    ChunkType.ERROR: 4,
    ChunkType.LOG: 1,
}

# Decay factors for graph traversal
HOP_DECAY = {
    1: 0.9,   # Direct dependencies
    2: 0.7,   # Two hops away
    3: 0.5,   # Three hops away
}


@dataclass
class ScoredChunk:
    """A chunk with its relevance score."""
    chunk: KnowledgeChunk
    score: float
    source: str  # "direct", "bm25", "graph_hop_1", etc.

    def __lt__(self, other):
        return self.score < other.score


class ContextRetriever:
    """
    Retrieves task-relevant context from the Knowledge Graph.

    Features:
    - BM25 text search for relevance
    - Multi-hop graph traversal for dependencies
    - Token budget management
    - Omission transparency (CRITICAL)
    - Progressive compression
    """

    def __init__(self, project_path: Path, storage: ChunkStorage):
        """
        Initialize context retriever.

        Args:
            project_path: Root path of the project
            storage: ChunkStorage instance
        """
        self.project_path = project_path
        self.storage = storage
        self._bm25_index: Optional[Any] = None
        self._chunk_id_map: List[str] = []

    def retrieve(
        self,
        task: str,
        token_budget: int = 30000,
        include_types: Optional[List[ChunkType]] = None,
        exclude_types: Optional[List[ChunkType]] = None,
        include_tests: bool = True,
        include_history: bool = False,
        compression: CompressionLevel = CompressionLevel.FULL,
        max_hops: int = 2,
        symbols: Optional[List[str]] = None,
        files: Optional[List[str]] = None,
    ) -> ContextBundle:
        """
        Retrieve task-relevant context with full omission transparency.

        Args:
            task: What the AI is trying to accomplish
            token_budget: Maximum tokens to return
            include_types: Only include these chunk types
            exclude_types: Exclude these chunk types
            include_tests: Include related test chunks
            include_history: Include commit history
            compression: Compression level for content
            max_hops: Maximum graph traversal depth
            symbols: Specific symbols to include
            files: Specific files to include

        Returns:
            ContextBundle with chunks, omissions, and expansions
        """
        start_time = time.time()

        # Early return for zero budget
        if token_budget <= 0:
            return ContextBundle(
                chunks=[],
                edges=[],
                total_tokens=0,
                omitted_chunks=[],
                omission_summary="Zero token budget - no chunks loaded.",
                omission_by_type={},
                omission_by_reason={},
                available_expansions=[],
                related_tests=[],
                related_commits=[],
                business_rules=[],
                task=task,
                token_budget=0,
                compression_level=compression,
                retrieval_time_ms=int((time.time() - start_time) * 1000),
            )

        # Build default type filters
        if include_types is None:
            include_types = [
                ChunkType.FUNCTION, ChunkType.CLASS, ChunkType.SOURCE_FILE,
                ChunkType.CONTRACT, ChunkType.CONFIG, ChunkType.METADATA,
            ]
            if include_tests:
                include_types.append(ChunkType.TEST)
            if include_history:
                include_types.append(ChunkType.COMMIT)

        if exclude_types:
            include_types = [t for t in include_types if t not in exclude_types]

        # Phase 1: Find entry points
        entry_points = self._find_entry_points(task, symbols, files)

        # Phase 2: BM25 search for relevance
        bm25_results = self._bm25_search(task, include_types, limit=50)

        # Phase 3: Graph expansion
        scored_chunks = self._expand_and_score(
            entry_points, bm25_results, max_hops, include_types
        )

        # Phase 4: Budget allocation with omission tracking
        bundle = self._allocate_budget(
            scored_chunks,
            token_budget,
            compression,
            include_types,
            task
        )

        # Phase 5: Build expansion options
        bundle.available_expansions = self._build_expansion_options(
            bundle.chunks, bundle.omitted_chunks
        )

        # Phase 6: Find related context IDs
        bundle.related_tests = self._find_related_tests(bundle.chunks)
        bundle.related_commits = self._find_related_commits(bundle.chunks)
        bundle.business_rules = self._find_related_rules(bundle.chunks)

        # Metadata
        bundle.task = task
        bundle.token_budget = token_budget
        bundle.compression_level = compression
        bundle.retrieval_time_ms = int((time.time() - start_time) * 1000)

        return bundle

    def _find_entry_points(
        self,
        task: str,
        symbols: Optional[List[str]],
        files: Optional[List[str]]
    ) -> List[ScoredChunk]:
        """Find direct entry points from task description."""
        entry_points: List[ScoredChunk] = []

        # Explicit symbols
        if symbols:
            for symbol in symbols:
                chunks = self.storage.search_symbol(symbol, exact=True)
                for chunk in chunks:
                    entry_points.append(ScoredChunk(
                        chunk=chunk,
                        score=10.0,
                        source="direct_symbol"
                    ))

        # Explicit files
        if files:
            for file_path in files:
                chunks = self.storage.get_chunks_by_file(file_path)
                for chunk in chunks:
                    entry_points.append(ScoredChunk(
                        chunk=chunk,
                        score=10.0,
                        source="direct_file"
                    ))

        # Extract potential symbols from task
        potential_symbols = self._extract_symbols_from_task(task)
        for symbol in potential_symbols:
            chunks = self.storage.search_symbol(symbol, exact=False)
            for chunk in chunks[:3]:  # Limit per symbol
                entry_points.append(ScoredChunk(
                    chunk=chunk,
                    score=5.0,
                    source="inferred_symbol"
                ))

        # Extract potential file paths from task
        potential_files = self._extract_files_from_task(task)
        for file_path in potential_files:
            chunks = self.storage.get_chunks_by_file(file_path)
            for chunk in chunks:
                entry_points.append(ScoredChunk(
                    chunk=chunk,
                    score=5.0,
                    source="inferred_file"
                ))

        return entry_points

    def _bm25_search(
        self,
        query: str,
        include_types: List[ChunkType],
        limit: int = 50
    ) -> List[ScoredChunk]:
        """Search using BM25 or FTS5 fallback."""
        results: List[ScoredChunk] = []

        # Use FTS5 search from storage
        search_results = self.storage.search_content(
            query,
            chunk_types=include_types,
            limit=limit
        )

        for chunk, score in search_results:
            results.append(ScoredChunk(
                chunk=chunk,
                score=score,
                source="bm25"
            ))

        return results

    def _expand_and_score(
        self,
        entry_points: List[ScoredChunk],
        bm25_results: List[ScoredChunk],
        max_hops: int,
        include_types: List[ChunkType]
    ) -> List[ScoredChunk]:
        """Expand from entry points using graph traversal."""
        all_scored: Dict[str, ScoredChunk] = {}

        # Add entry points
        for sc in entry_points:
            if sc.chunk.id not in all_scored or sc.score > all_scored[sc.chunk.id].score:
                all_scored[sc.chunk.id] = sc

        # Add BM25 results
        for sc in bm25_results:
            if sc.chunk.id not in all_scored or sc.score > all_scored[sc.chunk.id].score:
                all_scored[sc.chunk.id] = sc

        # Graph expansion
        frontier = list(all_scored.values())

        for hop in range(1, max_hops + 1):
            next_frontier: List[ScoredChunk] = []
            decay = HOP_DECAY.get(hop, 0.3)

            for sc in frontier:
                # Get outgoing edges
                edges = self.storage.get_edges_from(sc.chunk.id)
                for edge in edges:
                    target_chunk = self.storage.get_chunk(edge.target_id)
                    if not target_chunk:
                        continue

                    if target_chunk.chunk_type not in include_types:
                        continue

                    new_score = sc.score * decay * edge.weight
                    source = f"graph_hop_{hop}"

                    if target_chunk.id not in all_scored:
                        new_sc = ScoredChunk(
                            chunk=target_chunk,
                            score=new_score,
                            source=source
                        )
                        all_scored[target_chunk.id] = new_sc
                        next_frontier.append(new_sc)
                    elif new_score > all_scored[target_chunk.id].score:
                        all_scored[target_chunk.id].score = new_score
                        all_scored[target_chunk.id].source = source

                # Get incoming edges (dependents)
                edges_in = self.storage.get_edges_to(sc.chunk.id)
                for edge in edges_in:
                    source_chunk = self.storage.get_chunk(edge.source_id)
                    if not source_chunk:
                        continue

                    if source_chunk.chunk_type not in include_types:
                        continue

                    new_score = sc.score * decay * 0.5 * edge.weight  # Lower weight for dependents
                    source = f"graph_hop_{hop}_dependent"

                    if source_chunk.id not in all_scored:
                        new_sc = ScoredChunk(
                            chunk=source_chunk,
                            score=new_score,
                            source=source
                        )
                        all_scored[source_chunk.id] = new_sc
                        next_frontier.append(new_sc)

            frontier = next_frontier

        return sorted(all_scored.values(), key=lambda x: x.score, reverse=True)

    def _allocate_budget(
        self,
        scored_chunks: List[ScoredChunk],
        token_budget: int,
        compression: CompressionLevel,
        include_types: List[ChunkType],
        task: str
    ) -> ContextBundle:
        """
        Allocate token budget to chunks, tracking omissions.

        CRITICAL: Every omitted chunk must be tracked with reason.
        """
        bundle = ContextBundle()
        used_tokens = 0

        included_chunks: List[KnowledgeChunk] = []
        omitted_chunks: List[OmittedChunk] = []
        omission_by_type: Dict[str, int] = defaultdict(int)
        omission_by_reason: Dict[str, int] = defaultdict(int)

        # Sort by score and type priority
        for sc in scored_chunks:
            chunk = sc.chunk

            # Determine token cost based on compression
            if compression == CompressionLevel.FULL:
                token_cost = chunk.token_count
            elif compression == CompressionLevel.NO_COMMENTS:
                token_cost = int(chunk.token_count * 0.8)  # Estimate
            else:
                token_cost = chunk.token_count_compressed or int(chunk.token_count * 0.3)

            # Check if we can fit this chunk
            if used_tokens + token_cost <= token_budget:
                included_chunks.append(chunk)
                used_tokens += token_cost
            else:
                # Track omission with reason
                if token_cost > (token_budget - used_tokens):
                    reason = OmissionReason.TOKEN_BUDGET
                elif sc.score < 0.5:
                    reason = OmissionReason.LOW_RELEVANCE
                else:
                    reason = OmissionReason.TOKEN_BUDGET

                omitted = OmittedChunk(
                    id=chunk.id,
                    chunk_type=chunk.chunk_type,
                    reason=reason,
                    token_count=token_cost,
                    relevance_score=sc.score,
                    can_expand=True,
                    file_path=chunk.file_path,
                    symbol_name=chunk.symbol_name,
                )
                omitted_chunks.append(omitted)
                omission_by_type[chunk.chunk_type.value] += 1
                omission_by_reason[reason.value] += 1

        # Get edges for included chunks
        included_ids = {c.id for c in included_chunks}
        edges: List[ChunkEdge] = []
        for chunk in included_chunks:
            chunk_edges = self.storage.get_edges_from(chunk.id)
            for edge in chunk_edges:
                if edge.target_id in included_ids:
                    edges.append(edge)

        # Build omission summary
        if omitted_chunks:
            total_omitted_tokens = sum(o.token_count for o in omitted_chunks)
            omission_summary = (
                f"{len(omitted_chunks)} chunks omitted ({total_omitted_tokens:,} tokens). "
                f"Primary reason: {max(omission_by_reason, key=omission_by_reason.get) if omission_by_reason else 'none'}. "
                f"Use kg.expand to load specific chunks."
            )
        else:
            omission_summary = "All relevant chunks were loaded."

        bundle.chunks = included_chunks
        bundle.edges = edges
        bundle.total_tokens = used_tokens
        bundle.omitted_chunks = omitted_chunks
        bundle.omission_summary = omission_summary
        bundle.omission_by_type = dict(omission_by_type)
        bundle.omission_by_reason = dict(omission_by_reason)

        return bundle

    def _build_expansion_options(
        self,
        included: List[KnowledgeChunk],
        omitted: List[OmittedChunk]
    ) -> List[ExpansionOption]:
        """Build suggestions for what context could be expanded."""
        options: List[ExpansionOption] = []

        included_ids = {c.id for c in included}

        # High-value omitted chunks
        high_value = sorted(omitted, key=lambda x: x.relevance_score, reverse=True)[:5]
        for o in high_value:
            options.append(ExpansionOption(
                chunk_id=o.id,
                expansion_type="omitted",
                description=f"High relevance chunk ({o.relevance_score:.2f})",
                token_cost=o.token_count,
                priority=1,
            ))

        # Dependencies of included chunks that aren't included
        for chunk in included[:10]:  # Check first 10
            edges = self.storage.get_edges_from(chunk.id)
            for edge in edges:
                if edge.target_id not in included_ids:
                    target = self.storage.get_chunk(edge.target_id)
                    if target:
                        options.append(ExpansionOption(
                            chunk_id=edge.target_id,
                            expansion_type="dependency",
                            description=f"{edge.edge_type.value} from {chunk.symbol_name or chunk.id}",
                            token_cost=target.token_count,
                            priority=2,
                        ))

        # Related tests
        for chunk in included[:5]:
            test_edges = self.storage.get_edges_to(chunk.id, EdgeType.TESTED_BY)
            for edge in test_edges:
                if edge.source_id not in included_ids:
                    test = self.storage.get_chunk(edge.source_id)
                    if test:
                        options.append(ExpansionOption(
                            chunk_id=edge.source_id,
                            expansion_type="test",
                            description=f"Test for {chunk.symbol_name or chunk.id}",
                            token_cost=test.token_count,
                            priority=2,
                        ))

        return options[:20]  # Limit suggestions

    def _find_related_tests(self, chunks: List[KnowledgeChunk]) -> List[str]:
        """Find test IDs related to included chunks."""
        test_ids: Set[str] = set()

        for chunk in chunks:
            edges = self.storage.get_edges_to(chunk.id, EdgeType.TESTED_BY)
            for edge in edges:
                test_ids.add(edge.source_id)

        return list(test_ids)

    def _find_related_commits(self, chunks: List[KnowledgeChunk]) -> List[str]:
        """Find commit IDs related to included chunks."""
        commit_ids: Set[str] = set()

        for chunk in chunks:
            edges = self.storage.get_edges_from(chunk.id, EdgeType.MODIFIED_IN)
            for edge in edges:
                commit_ids.add(edge.target_id)

        return list(commit_ids)

    def _find_related_rules(self, chunks: List[KnowledgeChunk]) -> List[str]:
        """Find business rule IDs related to included chunks."""
        rule_ids: Set[str] = set()

        for chunk in chunks:
            edges = self.storage.get_edges_to(chunk.id, EdgeType.VALIDATES)
            for edge in edges:
                rule_ids.add(edge.source_id)

        return list(rule_ids)

    def _extract_symbols_from_task(self, task: str) -> List[str]:
        """Extract potential symbol names from task description."""
        # Match camelCase, snake_case, PascalCase identifiers
        patterns = [
            r'\b([A-Z][a-z]+[A-Z][a-zA-Z]*)\b',  # PascalCase
            r'\b([a-z]+_[a-z_]+)\b',               # snake_case
            r'\b([a-z]+[A-Z][a-zA-Z]*)\b',         # camelCase
            r'`([^`]+)`',                          # Backtick-quoted
        ]

        symbols: Set[str] = set()
        for pattern in patterns:
            matches = re.findall(pattern, task)
            symbols.update(matches)

        # Filter out common words
        common_words = {"the", "and", "for", "this", "that", "with", "from"}
        return [s for s in symbols if s.lower() not in common_words]

    def _extract_files_from_task(self, task: str) -> List[str]:
        """Extract potential file paths from task description."""
        # Match file path patterns
        patterns = [
            r'([a-zA-Z0-9_/.-]+\.(py|ts|js|tsx|jsx|rs|go|java|rb))',
            r'`([^`]+\.[a-z]+)`',
        ]

        files: Set[str] = set()
        for pattern in patterns:
            matches = re.findall(pattern, task)
            for match in matches:
                if isinstance(match, tuple):
                    files.add(match[0])
                else:
                    files.add(match)

        return list(files)

    def expand(
        self,
        chunk_id: str,
        expansion_type: str = "all",
        token_budget: int = 5000
    ) -> ContextBundle:
        """
        Expand context from a specific chunk.

        Args:
            chunk_id: Starting chunk ID
            expansion_type: "dependencies", "dependents", "tests", "all"
            token_budget: Maximum tokens

        Returns:
            ContextBundle with expanded context
        """
        bundle = ContextBundle()
        used_tokens = 0
        chunks: List[KnowledgeChunk] = []
        omitted: List[OmittedChunk] = []

        # Get the starting chunk
        start_chunk = self.storage.get_chunk(chunk_id)
        if not start_chunk:
            bundle.omission_summary = f"Chunk not found: {chunk_id}"
            return bundle

        chunks.append(start_chunk)
        used_tokens += start_chunk.token_count

        # Get related chunks based on expansion type
        related_ids: Set[str] = set()

        if expansion_type in ("dependencies", "all"):
            edges = self.storage.get_edges_from(chunk_id)
            for edge in edges:
                related_ids.add(edge.target_id)

        if expansion_type in ("dependents", "all"):
            edges = self.storage.get_edges_to(chunk_id)
            for edge in edges:
                related_ids.add(edge.source_id)

        if expansion_type in ("tests", "all"):
            edges = self.storage.get_edges_to(chunk_id, EdgeType.TESTED_BY)
            for edge in edges:
                related_ids.add(edge.source_id)

        # Load related chunks with budget
        for related_id in related_ids:
            related_chunk = self.storage.get_chunk(related_id)
            if not related_chunk:
                continue

            if used_tokens + related_chunk.token_count <= token_budget:
                chunks.append(related_chunk)
                used_tokens += related_chunk.token_count
            else:
                omitted.append(OmittedChunk(
                    id=related_chunk.id,
                    chunk_type=related_chunk.chunk_type,
                    reason=OmissionReason.TOKEN_BUDGET,
                    token_count=related_chunk.token_count,
                    can_expand=True,
                    file_path=related_chunk.file_path,
                    symbol_name=related_chunk.symbol_name,
                ))

        bundle.chunks = chunks
        bundle.total_tokens = used_tokens
        bundle.omitted_chunks = omitted
        bundle.omission_summary = bundle.get_omission_stats()
        bundle.task = f"expand:{chunk_id}:{expansion_type}"
        bundle.token_budget = token_budget

        return bundle


async def retrieve_context(
    project_path: str,
    task: str,
    token_budget: int = 30000,
    include_types: Optional[List[str]] = None,
    exclude_types: Optional[List[str]] = None,
    include_tests: bool = True,
    compression: int = 0,
    symbols: Optional[List[str]] = None,
    files: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Retrieve task-relevant context from the Knowledge Graph.

    Args:
        project_path: Path to the project
        task: What you're trying to accomplish
        token_budget: Maximum tokens (default 30000)
        include_types: Chunk types to include
        exclude_types: Chunk types to exclude
        include_tests: Include related tests
        compression: 0=full, 1=no_comments, 2=signatures
        symbols: Specific symbols to include
        files: Specific files to include

    Returns:
        Dictionary with context bundle data
    """
    path = Path(project_path)
    storage = ChunkStorage(path)
    retriever = ContextRetriever(path, storage)

    # Convert type strings to enums
    include_type_enums = None
    if include_types:
        include_type_enums = [ChunkType(t) for t in include_types]

    exclude_type_enums = None
    if exclude_types:
        exclude_type_enums = [ChunkType(t) for t in exclude_types]

    compression_level = CompressionLevel(compression)

    bundle = retriever.retrieve(
        task=task,
        token_budget=token_budget,
        include_types=include_type_enums,
        exclude_types=exclude_type_enums,
        include_tests=include_tests,
        compression=compression_level,
        symbols=symbols,
        files=files,
    )

    # Build executive summary
    loaded = len(bundle.chunks)
    omitted = len(bundle.omitted_chunks)
    total = loaded + omitted
    coverage_pct = round(loaded * 100 / total) if total > 0 else 0

    # Get top relevant files (unique, ordered by relevance)
    seen_files = set()
    top_relevant = []
    for chunk in bundle.chunks[:10]:
        if chunk.file_path and chunk.file_path not in seen_files:
            seen_files.add(chunk.file_path)
            top_relevant.append(chunk.file_path)
            if len(top_relevant) >= 5:
                break

    # Get suggested expansions (top 3 with highest token cost)
    suggested_expansions = sorted(
        bundle.available_expansions,
        key=lambda x: x.token_cost,
        reverse=True
    )[:3]

    return {
        "success": True,
        # Executive summary at top for quick understanding
        "executive_summary": {
            "loaded": loaded,
            "omitted": omitted,
            "coverage": f"{coverage_pct}%",
            "tokens_used": bundle.total_tokens,
            "token_budget": bundle.token_budget,
            "retrieval_time_ms": bundle.retrieval_time_ms,
            "top_relevant_files": top_relevant,
        },
        "context_markdown": bundle.to_markdown(),
        "stats": {
            "chunks_loaded": loaded,
            "chunks_omitted": omitted,
            "tokens_used": bundle.total_tokens,
            "token_budget": bundle.token_budget,
            "retrieval_time_ms": bundle.retrieval_time_ms,
        },
        "omission_summary": bundle.omission_summary,
        "omission_by_type": bundle.omission_by_type,
        "omission_by_reason": bundle.omission_by_reason,
        "suggested_expansions": [
            {
                "chunk_id": e.chunk_id,
                "type": e.expansion_type,
                "description": e.description,
                "token_cost": e.token_cost,
            }
            for e in suggested_expansions
        ],
        "available_expansions": [e.to_dict() for e in bundle.available_expansions],
        "related_tests": bundle.related_tests,
        "related_commits": bundle.related_commits,
        "business_rules": bundle.business_rules,
    }
