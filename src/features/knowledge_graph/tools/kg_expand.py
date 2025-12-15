"""
MCP Tool: kg.expand

Expand context from a specific chunk (dependencies, dependents, tests).
"""

from typing import Any, Dict, Literal
from pathlib import Path

from src.features.knowledge_graph import ChunkStorage, ContextRetriever


async def kg_expand(
    project_path: str,
    chunk_id: str,
    expansion_type: Literal["dependencies", "dependents", "tests", "all"] = "all",
    token_budget: int = 5000
) -> Dict[str, Any]:
    """
    Expand context from a specific chunk.

    Use this to load additional context related to a chunk you already have.
    Especially useful for following up on omitted chunks from kg.retrieve.

    Args:
        project_path: Path to CFA project
        chunk_id: ID of the chunk to expand from
        expansion_type: What to expand:
            - "dependencies": Chunks this depends on
            - "dependents": Chunks that depend on this
            - "tests": Test chunks for this code
            - "all": All of the above
        token_budget: Maximum tokens for expansion (default 5000)

    Returns:
        Dictionary with:
            - success: Boolean
            - context_markdown: Expanded context in markdown
            - chunks_loaded: Number of chunks loaded
            - chunks_omitted: Number of chunks that couldn't fit
            - omission_summary: What was omitted

    Examples:
        # Expand from an omitted chunk
        result = await kg_expand(
            project_path="/projects/my-app",
            chunk_id="src/auth.py:authenticate",
            expansion_type="dependencies"
        )

        # Load tests for a function
        result = await kg_expand(
            project_path="/projects/my-app",
            chunk_id="src/user.py:validate_email",
            expansion_type="tests"
        )

        # Full expansion
        result = await kg_expand(
            project_path="/projects/my-app",
            chunk_id="src/core/database.py",
            expansion_type="all",
            token_budget=10000
        )

    Best Practice:
        1. Use after kg.retrieve to dig deeper
        2. Check available_expansions from kg.retrieve
        3. Start with "dependencies" for understanding code
        4. Use "tests" to understand expected behavior
    """
    try:
        path = Path(project_path)

        # Validate CFA project
        if not (path / ".claude").exists():
            return {
                "success": False,
                "error": "Not a CFA project (missing .claude/)"
            }

        # Check if knowledge graph exists
        db_path = path / ".claude" / "knowledge_graph.db"
        if not db_path.exists():
            return {
                "success": False,
                "error": "Knowledge Graph not built yet. Run kg.build first."
            }

        storage = ChunkStorage(path)
        retriever = ContextRetriever(path, storage)

        # Expand from chunk
        bundle = retriever.expand(
            chunk_id=chunk_id,
            expansion_type=expansion_type,
            token_budget=token_budget
        )

        return {
            "success": True,
            "context_markdown": bundle.to_markdown(),
            "chunks_loaded": len(bundle.chunks),
            "chunks_omitted": len(bundle.omitted_chunks),
            "tokens_used": bundle.total_tokens,
            "omission_summary": bundle.omission_summary,
            "omitted_chunks": [o.to_dict() for o in bundle.omitted_chunks],
        }

    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to expand chunk: {str(e)}"
        }
