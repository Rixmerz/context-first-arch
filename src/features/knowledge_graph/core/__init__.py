"""
Knowledge Graph Core Module - Business Logic Layer

Graph-based context retrieval with chunking,
multi-hop traversal, and omission transparency.
"""

from .models import (
    ChunkType,
    EdgeType,
    CompressionLevel,
    OmissionReason,
    KnowledgeChunk,
    ChunkEdge,
    OmittedChunk,
    ExpansionOption,
    ContextBundle,
    GraphStats,
)
from .storage import ChunkStorage
from .chunker import (
    CodeChunker,
    ContractChunker,
    ConfigChunker,
    chunk_project,
    estimate_tokens,
)
from .graph_builder import GraphBuilder, build_knowledge_graph
from .retriever import ContextRetriever, retrieve_context
from .compressor import (
    compress_chunk,
    strip_comments,
    extract_signature,
    estimate_compressed_tokens,
)
from .git_chunker import GitChunker
from .business_rules import (
    BusinessRule,
    BusinessRuleStore,
    RuleStatus,
    RuleCategory,
    interpret_rules_from_code,
)

__all__ = [
    # Enums
    "ChunkType", "EdgeType", "CompressionLevel", "OmissionReason",
    # Core Models
    "KnowledgeChunk", "ChunkEdge", "OmittedChunk", "ExpansionOption", "ContextBundle", "GraphStats",
    # Storage
    "ChunkStorage",
    # Chunkers
    "CodeChunker", "ContractChunker", "ConfigChunker", "chunk_project", "estimate_tokens",
    # Graph Builder
    "GraphBuilder", "build_knowledge_graph",
    # Retriever
    "ContextRetriever", "retrieve_context",
    # Compressor
    "compress_chunk", "strip_comments", "extract_signature", "estimate_compressed_tokens",
    # Git History
    "GitChunker",
    # Business Rules
    "BusinessRule", "BusinessRuleStore", "RuleStatus", "RuleCategory", "interpret_rules_from_code",
]
