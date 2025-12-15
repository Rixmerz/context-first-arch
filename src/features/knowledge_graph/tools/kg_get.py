"""
MCP Tool: kg.get

Get specific chunks by ID.
"""

from typing import Any, Dict, List
from pathlib import Path

from src.features.knowledge_graph import ChunkStorage


async def kg_get(
    project_path: str,
    chunk_ids: List[str]
) -> Dict[str, Any]:
    """
    Get specific chunks by ID.

    Use when you know exactly which chunks you need.
    More efficient than kg.retrieve for targeted loading.

    Args:
        project_path: Path to CFA project
        chunk_ids: List of chunk IDs to retrieve

    Returns:
        Dictionary with:
            - success: Boolean
            - chunks: List of chunk data
            - found: Number of chunks found
            - not_found: List of IDs that weren't found

    Examples:
        # Get specific chunks
        result = await kg_get(
            project_path="/projects/my-app",
            chunk_ids=[
                "src/auth.py:authenticate",
                "src/user.py:User",
                "config:settings.py"
            ]
        )

        # Load omitted chunks from previous retrieve
        omitted_ids = [o["id"] for o in previous_result["omitted_chunks"][:5]]
        result = await kg_get(
            project_path="/projects/my-app",
            chunk_ids=omitted_ids
        )

    Best Practice:
        Use this for precise loading when you have chunk IDs from:
        - kg.retrieve omitted_chunks
        - kg.search results
        - kg.expand suggestions
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

        # Get chunks
        chunks = storage.get_chunks(chunk_ids)
        found_ids = {c.id for c in chunks}
        not_found = [cid for cid in chunk_ids if cid not in found_ids]

        # Format chunks for output
        chunk_data = []
        total_tokens = 0

        for chunk in chunks:
            chunk_data.append({
                "id": chunk.id,
                "type": chunk.chunk_type.value,
                "file_path": chunk.file_path,
                "symbol_name": chunk.symbol_name,
                "line_range": f"{chunk.line_start}-{chunk.line_end}" if chunk.line_start else None,
                "token_count": chunk.token_count,
                "content": chunk.content,
                "signature": chunk.signature,
                "docstring": chunk.docstring,
                "tags": chunk.tags,
            })
            total_tokens += chunk.token_count

        return {
            "success": True,
            "chunks": chunk_data,
            "found": len(chunks),
            "not_found": not_found,
            "total_tokens": total_tokens,
            "message": f"Retrieved {len(chunks)}/{len(chunk_ids)} chunks ({total_tokens:,} tokens)"
        }

    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to get chunks: {str(e)}"
        }
