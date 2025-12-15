"""
Knowledge Graph Feature - Intelligent Context Retrieval

Graph-based context chunking and retrieval system for CFA v3.

## Architecture (CFA v2 Pattern)

```
features/knowledge_graph/
├── core/
│   ├── models.py           # Chunk types and data models
│   ├── storage.py          # SQLite graph storage
│   ├── chunker.py          # Code/contract/config chunkers
│   ├── graph_builder.py    # Graph construction
│   ├── retriever.py        # BM25 + graph retrieval
│   ├── compressor.py       # Token optimization
│   ├── git_chunker.py      # Git history integration
│   ├── business_rules.py   # Rule extraction
│   ├── timeline.py         # Snapshot management
│   └── watcher.py          # File watching
├── tools/
│   └── kg_*.py             # 12 MCP tools
└── tests/
```

## Usage

```python
from src.features.knowledge_graph import build_knowledge_graph, retrieve_context

# Build the graph
build_knowledge_graph(project_path)

# Retrieve context for a task
context = retrieve_context(project_path, "implement user auth", token_budget=30000)
```
"""

from .core import (
    # Enums
    ChunkType, EdgeType, CompressionLevel, OmissionReason,
    # Core Models
    KnowledgeChunk, ChunkEdge, OmittedChunk, ExpansionOption, ContextBundle, GraphStats,
    # Storage
    ChunkStorage,
    # Chunkers
    CodeChunker, ContractChunker, ConfigChunker, chunk_project, estimate_tokens,
    # Graph Builder
    GraphBuilder, build_knowledge_graph,
    # Retriever
    ContextRetriever, retrieve_context,
    # Compressor
    compress_chunk, strip_comments, extract_signature, estimate_compressed_tokens,
    # Git History
    GitChunker,
    # Business Rules
    BusinessRule, BusinessRuleStore, RuleStatus, RuleCategory, interpret_rules_from_code,
    # Timeline
    Snapshot, SnapshotType, FileState, TimelineManager,
    # Watcher
    KGWatcher, get_watcher, start_watcher, stop_watcher, get_watcher_status,
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
    # Timeline
    "Snapshot", "SnapshotType", "FileState", "TimelineManager",
    # Watcher
    "KGWatcher", "get_watcher", "start_watcher", "stop_watcher", "get_watcher_status",
]
