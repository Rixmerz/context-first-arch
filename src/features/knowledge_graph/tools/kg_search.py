"""
MCP Tool: kg.search

Search the Knowledge Graph using BM25 + FTS5.
"""

from typing import Any, Dict, List, Optional
from pathlib import Path

from src.features.knowledge_graph import ChunkStorage, ChunkType


async def kg_search(
    project_path: str,
    query: str,
    chunk_types: Optional[List[str]] = None,
    limit: int = 20
) -> Dict[str, Any]:
    """
    Search the Knowledge Graph using BM25 ranking.

    Full-text search across all chunks with relevance scoring.
    Returns chunk IDs and metadata without full content.

    Args:
        project_path: Path to CFA project
        query: Search query (supports natural language)
        chunk_types: Filter by types (e.g., ["function", "test", "config"])
        limit: Maximum results (default 20)

    Returns:
        Dictionary with:
            - success: Boolean
            - results: List of matching chunks with scores
            - total_found: Number of matches

    Examples:
        # Search for authentication-related code
        result = await kg_search(
            project_path="/projects/my-app",
            query="authentication login user validation"
        )

        # Search only in tests
        result = await kg_search(
            project_path="/projects/my-app",
            query="email validation",
            chunk_types=["test"]
        )

        # Search config files
        result = await kg_search(
            project_path="/projects/my-app",
            query="database connection",
            chunk_types=["config", "metadata"]
        )

    Best Practice:
        1. Use natural language queries
        2. Filter by chunk_types for focused search
        3. Use results with kg.get to load full content
        4. Combine multiple keywords for better results
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

        # Convert type strings to enums
        type_enums = None
        if chunk_types:
            type_enums = [ChunkType(t) for t in chunk_types]

        # Search
        results = storage.search_content(
            query=query,
            chunk_types=type_enums,
            limit=limit
        )

        # Format results
        formatted_results = []
        for chunk, score in results:
            formatted_results.append({
                "id": chunk.id,
                "type": chunk.chunk_type.value,
                "score": round(score, 3),
                "file_path": chunk.file_path,
                "symbol_name": chunk.symbol_name,
                "line_range": f"{chunk.line_start}-{chunk.line_end}" if chunk.line_start else None,
                "token_count": chunk.token_count,
                "preview": chunk.content[:200] + "..." if len(chunk.content) > 200 else chunk.content,
                "tags": chunk.tags,
            })

        return {
            "success": True,
            "query": query,
            "results": formatted_results,
            "total_found": len(formatted_results),
            "message": f"Found {len(formatted_results)} results for '{query}'"
        }

    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to search: {str(e)}"
        }
