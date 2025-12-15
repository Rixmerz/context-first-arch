"""
Knowledge Graph Models for CFA v3.

Defines the 10 chunk types, edge types, and core data structures
for the Project Knowledge Graph system.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple


class ChunkType(Enum):
    """
    10 types of knowledge chunks that capture different project dimensions.

    Priority Legend:
    - P1: Core (Phase 1) - Essential for MVP
    - P2: Extended (Phase 2) - History integration
    - P3: Advanced (Phase 3) - Business rules
    - P4: Future (Phase 4) - Timeline/snapshots
    """

    # === Code Layer (P1) ===
    SOURCE_FILE = "source_file"      # Complete file, maximum fidelity
    FUNCTION = "function"            # Function/method entity
    CLASS = "class"                  # Class with methods

    # === Structure Layer (P1/P2) ===
    AST = "ast"                      # Compressed AST for structural analysis
    CALLGRAPH = "callgraph"          # Static call graph
    DEPENDENCY = "dependency"        # Import/require relationships

    # === Spec Layer (P1) ===
    TEST = "test"                    # Test file/suite with expectations
    CONTRACT = "contract"            # CFA contract definition

    # === Context Layer (P1) ===
    CONFIG = "config"                # ENV, settings, feature flags
    METADATA = "metadata"            # package.json, pyproject.toml, etc.

    # === History Layer (P2) ===
    COMMIT = "commit"                # Git commit information

    # === Knowledge Layer (P3) ===
    BUSINESS_RULE = "business_rule"  # Human-confirmed business rule

    # === Timeline Layer (P4) ===
    SNAPSHOT_USER = "snapshot_user"      # User intent timeline
    SNAPSHOT_AGENT = "snapshot_agent"    # Agent execution timeline

    # === Debug Layer (P4) ===
    ERROR = "error"                  # Stacktrace, crash info
    LOG = "log"                      # Runtime log


class EdgeType(Enum):
    """
    Relationship types between chunks in the Knowledge Graph.

    These edges enable multi-hop traversal for intelligent context retrieval.
    """

    # === Code Relationships ===
    CALLS = "calls"                  # Function A → calls → Function B
    IMPORTS = "imports"              # File A → imports → File B
    INHERITS = "inherits"            # Class A → inherits → Class B
    CONTAINS = "contains"            # Class → contains → Method

    # === Spec Relationships ===
    TESTED_BY = "tested_by"          # Code ← tested_by ← Test
    IMPLEMENTS = "implements"        # Code → implements → Contract
    VALIDATES = "validates"          # BusinessRule → validates → Code

    # === History Relationships ===
    MODIFIED_IN = "modified_in"      # Code → modified_in → Commit
    PRECEDED_BY = "preceded_by"      # Snapshot → preceded_by → Snapshot

    # === Context Relationships ===
    CONFIGURED_BY = "configured_by"  # Code → configured_by → Config
    FAILED_AT = "failed_at"          # Error → failed_at → Code


class OmissionReason(Enum):
    """Reasons why a chunk was omitted from the context bundle."""

    TOKEN_BUDGET = "token_budget"        # Exceeded token limit
    LOW_RELEVANCE = "low_relevance"      # Below relevance threshold
    LOW_PRIORITY = "low_priority"        # Lower priority chunk type
    COMPRESSION = "compression"          # Compressed to signature only
    EXCLUDED_TYPE = "excluded_type"      # Chunk type was excluded
    MAX_DEPTH = "max_depth"              # Beyond max graph traversal depth


class CompressionLevel(Enum):
    """Progressive disclosure levels for chunk content."""

    FULL = 0              # Full content with all comments
    NO_COMMENTS = 1       # Full code without comments
    SIGNATURE_DOCSTRING = 2  # Signature + docstring only
    SIGNATURE_ONLY = 3    # Just the signature


@dataclass
class KnowledgeChunk:
    """
    A single chunk in the Project Knowledge Graph.

    Represents any type of project knowledge with unified interface
    for storage, retrieval, and compression.
    """

    # Identity
    id: str                              # Unique: "file:symbol" or "file:line_start-line_end"
    chunk_type: ChunkType

    # Content (varies by type)
    content: str                         # Main content
    content_compressed: Optional[str] = None  # Signature/summary version
    token_count: int = 0                 # Full content tokens
    token_count_compressed: int = 0      # Compressed tokens

    # Location (for code chunks)
    file_path: Optional[str] = None
    line_start: Optional[int] = None
    line_end: Optional[int] = None
    symbol_name: Optional[str] = None

    # Signature (for functions/classes)
    signature: Optional[str] = None
    docstring: Optional[str] = None

    # Metadata
    created_at: str = ""                 # ISO timestamp
    updated_at: str = ""                 # ISO timestamp
    source: str = "auto"                 # "auto", "git", "human"
    confidence: float = 1.0              # For business rules: human confirmation level

    # CFA Integration
    feature: Optional[str] = None        # Feature area this belongs to
    tags: List[str] = field(default_factory=list)

    # Extra data (type-specific)
    extra: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Set timestamps if not provided."""
        if not self.created_at:
            self.created_at = datetime.now().isoformat()
        if not self.updated_at:
            self.updated_at = self.created_at

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "id": self.id,
            "chunk_type": self.chunk_type.value,
            "content": self.content,
            "content_compressed": self.content_compressed,
            "token_count": self.token_count,
            "token_count_compressed": self.token_count_compressed,
            "file_path": self.file_path,
            "line_start": self.line_start,
            "line_end": self.line_end,
            "symbol_name": self.symbol_name,
            "signature": self.signature,
            "docstring": self.docstring,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "source": self.source,
            "confidence": self.confidence,
            "feature": self.feature,
            "tags": self.tags,
            "extra": self.extra,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "KnowledgeChunk":
        """Create from dictionary."""
        data = data.copy()
        data["chunk_type"] = ChunkType(data["chunk_type"])
        return cls(**data)

    def get_content_at_level(self, level: CompressionLevel) -> str:
        """Get content at specified compression level."""
        if level == CompressionLevel.FULL:
            return self.content
        elif level == CompressionLevel.NO_COMMENTS:
            # Remove comments (basic implementation)
            return self._strip_comments(self.content)
        elif level == CompressionLevel.SIGNATURE_DOCSTRING:
            if self.signature and self.docstring:
                return f"{self.signature}\n    \"\"\"{self.docstring}\"\"\"\n    ..."
            return self.content_compressed or self.content
        else:  # SIGNATURE_ONLY
            return self.signature or self.content_compressed or self.content[:100]

    def _strip_comments(self, content: str) -> str:
        """Basic comment stripping (language-agnostic)."""
        lines = content.split("\n")
        result = []
        in_multiline = False

        for line in lines:
            stripped = line.strip()

            # Skip single-line comments
            if stripped.startswith("#") or stripped.startswith("//"):
                continue

            # Handle multi-line comments (basic)
            if "/*" in stripped or '"""' in stripped or "'''" in stripped:
                in_multiline = not in_multiline
                continue

            if not in_multiline:
                result.append(line)

        return "\n".join(result)


@dataclass
class ChunkEdge:
    """
    An edge connecting two chunks in the Knowledge Graph.
    """

    source_id: str                       # Source chunk ID
    target_id: str                       # Target chunk ID
    edge_type: EdgeType
    weight: float = 1.0                  # Edge weight for scoring
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "source_id": self.source_id,
            "target_id": self.target_id,
            "edge_type": self.edge_type.value,
            "weight": self.weight,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ChunkEdge":
        """Create from dictionary."""
        data = data.copy()
        data["edge_type"] = EdgeType(data["edge_type"])
        return cls(**data)


@dataclass
class OmittedChunk:
    """
    Information about a chunk that was NOT included in the context.

    CRITICAL: Omission transparency is essential - the AI must always
    know what it doesn't have access to and why.
    """

    id: str                              # Chunk ID
    chunk_type: ChunkType
    reason: OmissionReason
    token_count: int                     # How many tokens this would cost
    relevance_score: float = 0.0         # Why it was ranked lower
    can_expand: bool = True              # Can be loaded via kg.expand
    file_path: Optional[str] = None      # For navigation
    symbol_name: Optional[str] = None    # For understanding

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "chunk_type": self.chunk_type.value,
            "reason": self.reason.value,
            "token_count": self.token_count,
            "relevance_score": self.relevance_score,
            "can_expand": self.can_expand,
            "file_path": self.file_path,
            "symbol_name": self.symbol_name,
        }


@dataclass
class ExpansionOption:
    """
    An available expansion from the current context.

    Tells the AI what additional context is available and why
    it might be useful.
    """

    chunk_id: str
    expansion_type: str                  # "dependencies", "dependents", "tests", "history"
    description: str                     # Why this might be useful
    token_cost: int                      # How many tokens this would add
    priority: int = 1                    # 1 = high, 2 = medium, 3 = low

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "chunk_id": self.chunk_id,
            "expansion_type": self.expansion_type,
            "description": self.description,
            "token_cost": self.token_cost,
            "priority": self.priority,
        }


@dataclass
class ContextBundle:
    """
    The result of a context retrieval operation.

    Contains both what was retrieved AND what was omitted,
    enabling full transparency about available context.
    """

    # What you got
    chunks: List[KnowledgeChunk] = field(default_factory=list)
    edges: List[ChunkEdge] = field(default_factory=list)
    total_tokens: int = 0

    # CRITICAL: What you did NOT get
    omitted_chunks: List[OmittedChunk] = field(default_factory=list)
    omission_summary: str = ""
    omission_by_type: Dict[str, int] = field(default_factory=dict)
    omission_by_reason: Dict[str, int] = field(default_factory=dict)

    # Navigation and expansion
    available_expansions: List[ExpansionOption] = field(default_factory=list)

    # Related context (IDs only for navigation)
    related_tests: List[str] = field(default_factory=list)
    related_commits: List[str] = field(default_factory=list)
    business_rules: List[str] = field(default_factory=list)

    # Retrieval metadata
    task: str = ""                       # What task triggered this retrieval
    token_budget: int = 0                # What was the budget
    compression_level: CompressionLevel = CompressionLevel.FULL
    retrieval_time_ms: int = 0           # Performance tracking

    def to_markdown(self, include_omission_details: bool = True) -> str:
        """
        Convert bundle to markdown for context loading.

        This is the primary output format for AI consumption.
        """
        lines = []

        # Header with transparency
        lines.append("# Context Bundle")
        lines.append(f"**Task**: {self.task}")
        lines.append(f"**Tokens Used**: {self.total_tokens:,} / {self.token_budget:,}")
        lines.append(f"**Chunks Loaded**: {len(self.chunks)}")
        lines.append(f"**Chunks Omitted**: {len(self.omitted_chunks)}")
        lines.append("")

        # Omission transparency (CRITICAL)
        if self.omitted_chunks and include_omission_details:
            lines.append("## Omission Report")
            lines.append(f"*{self.omission_summary}*")
            lines.append("")

            if self.omission_by_type:
                lines.append("**By Type:**")
                for chunk_type, count in sorted(self.omission_by_type.items()):
                    lines.append(f"- {chunk_type}: {count}")
                lines.append("")

            if self.omission_by_reason:
                lines.append("**By Reason:**")
                for reason, count in sorted(self.omission_by_reason.items()):
                    lines.append(f"- {reason}: {count}")
                lines.append("")

            # Top omitted chunks for expansion
            high_value_omitted = [o for o in self.omitted_chunks if o.can_expand][:5]
            if high_value_omitted:
                lines.append("**Available for Expansion** (use `kg.expand`):")
                for omitted in high_value_omitted:
                    lines.append(f"- `{omitted.id}` ({omitted.token_count} tokens, {omitted.reason.value})")
                lines.append("")

        # Chunk content
        lines.append("---")
        lines.append("## Content")
        lines.append("")

        # Group by type
        chunks_by_type: Dict[ChunkType, List[KnowledgeChunk]] = {}
        for chunk in self.chunks:
            if chunk.chunk_type not in chunks_by_type:
                chunks_by_type[chunk.chunk_type] = []
            chunks_by_type[chunk.chunk_type].append(chunk)

        for chunk_type in ChunkType:
            if chunk_type in chunks_by_type:
                type_chunks = chunks_by_type[chunk_type]
                lines.append(f"### {chunk_type.value.upper()} ({len(type_chunks)})")
                lines.append("")

                for chunk in type_chunks:
                    # Chunk header
                    header = f"#### `{chunk.id}`"
                    if chunk.symbol_name:
                        header += f" - {chunk.symbol_name}"
                    lines.append(header)

                    if chunk.file_path and chunk.line_start:
                        lines.append(f"*{chunk.file_path}:{chunk.line_start}-{chunk.line_end}*")

                    lines.append("")
                    lines.append("```")
                    lines.append(chunk.get_content_at_level(self.compression_level))
                    lines.append("```")
                    lines.append("")

        # Available expansions
        if self.available_expansions:
            lines.append("---")
            lines.append("## Available Expansions")
            lines.append("")
            for exp in sorted(self.available_expansions, key=lambda x: x.priority):
                lines.append(f"- **{exp.expansion_type}** for `{exp.chunk_id}`: {exp.description} (+{exp.token_cost} tokens)")
            lines.append("")

        return "\n".join(lines)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "chunks": [c.to_dict() for c in self.chunks],
            "edges": [e.to_dict() for e in self.edges],
            "total_tokens": self.total_tokens,
            "omitted_chunks": [o.to_dict() for o in self.omitted_chunks],
            "omission_summary": self.omission_summary,
            "omission_by_type": self.omission_by_type,
            "omission_by_reason": self.omission_by_reason,
            "available_expansions": [e.to_dict() for e in self.available_expansions],
            "related_tests": self.related_tests,
            "related_commits": self.related_commits,
            "business_rules": self.business_rules,
            "task": self.task,
            "token_budget": self.token_budget,
            "compression_level": self.compression_level.value,
            "retrieval_time_ms": self.retrieval_time_ms,
        }

    def get_omission_stats(self) -> str:
        """Get human-readable omission statistics."""
        if not self.omitted_chunks:
            return "All relevant chunks were loaded."

        total_omitted_tokens = sum(o.token_count for o in self.omitted_chunks)
        expandable = sum(1 for o in self.omitted_chunks if o.can_expand)

        return (
            f"{len(self.omitted_chunks)} chunks omitted "
            f"({total_omitted_tokens:,} tokens). "
            f"{expandable} can be expanded with kg.expand."
        )


@dataclass
class GraphStats:
    """Statistics about the Knowledge Graph."""

    total_chunks: int = 0
    total_edges: int = 0
    chunks_by_type: Dict[str, int] = field(default_factory=dict)
    edges_by_type: Dict[str, int] = field(default_factory=dict)
    total_tokens: int = 0
    last_build: str = ""
    last_file_change: str = ""
    needs_rebuild: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "total_chunks": self.total_chunks,
            "total_edges": self.total_edges,
            "chunks_by_type": self.chunks_by_type,
            "edges_by_type": self.edges_by_type,
            "total_tokens": self.total_tokens,
            "last_build": self.last_build,
            "last_file_change": self.last_file_change,
            "needs_rebuild": self.needs_rebuild,
        }
