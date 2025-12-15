"""
MCP Tool: kg.status

Get Knowledge Graph status and statistics.
"""

from typing import Any, Dict
from pathlib import Path

from src.features.knowledge_graph import ChunkStorage


async def kg_status(project_path: str) -> Dict[str, Any]:
    """
    Get Knowledge Graph status and statistics.

    Shows current graph state including chunk counts, edge counts,
    and whether a rebuild is needed.

    Args:
        project_path: Path to CFA project

    Returns:
        Dictionary with:
            - success: Boolean
            - total_chunks: Total number of chunks
            - total_edges: Total number of edges
            - chunks_by_type: Breakdown by chunk type
            - edges_by_type: Breakdown by edge type
            - total_tokens: Total tokens in graph
            - last_build: When graph was last built
            - needs_rebuild: Whether files changed since last build

    Examples:
        result = await kg_status(project_path="/projects/my-app")

        if result["needs_rebuild"]:
            await kg_build(project_path)
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
                "success": True,
                "exists": False,
                "total_chunks": 0,
                "total_edges": 0,
                "needs_rebuild": True,
                "message": "Knowledge Graph not built yet. Run kg.build first."
            }

        # Get stats
        storage = ChunkStorage(path)
        stats = storage.get_stats()

        return {
            "success": True,
            "exists": True,
            "total_chunks": stats.total_chunks,
            "total_edges": stats.total_edges,
            "chunks_by_type": stats.chunks_by_type,
            "edges_by_type": stats.edges_by_type,
            "total_tokens": stats.total_tokens,
            "last_build": stats.last_build,
            "last_file_change": stats.last_file_change,
            "needs_rebuild": stats.needs_rebuild,
            "message": (
                f"Knowledge Graph: {stats.total_chunks} chunks, "
                f"{stats.total_edges} edges, "
                f"{stats.total_tokens:,} tokens. "
                f"{'Rebuild recommended.' if stats.needs_rebuild else 'Up to date.'}"
            )
        }

    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to get Knowledge Graph status: {str(e)}"
        }
