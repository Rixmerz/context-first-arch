"""
MCP Tool: kg.related

Find chunks related to a specific chunk (tests, commits, business rules).
"""

from typing import Any, Dict, List, Optional
from pathlib import Path

from src.features.knowledge_graph import ChunkStorage, EdgeType


async def kg_related(
    project_path: str,
    chunk_id: str,
    relation_types: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Find chunks related to a specific chunk.

    Discovers relationships through the Knowledge Graph edges:
    - Tests that cover this code
    - Commits that modified this code
    - Business rules that apply
    - Dependencies and dependents

    Args:
        project_path: Path to CFA project
        chunk_id: ID of the chunk to find relations for
        relation_types: Filter by relation types. Options:
            - "tests": Chunks that test this code
            - "dependencies": Chunks this depends on
            - "dependents": Chunks that depend on this
            - "commits": Commits that modified this
            - "rules": Business rules for this
            - "contracts": Contracts this implements

    Returns:
        Dictionary with:
            - success: Boolean
            - chunk_id: The queried chunk
            - relations: Dict of relation_type -> list of chunk IDs
            - details: Extended info for each relation

    Examples:
        # Find all relations
        result = await kg_related(
            project_path="/projects/my-app",
            chunk_id="src/auth.py:authenticate"
        )

        # Find only tests
        result = await kg_related(
            project_path="/projects/my-app",
            chunk_id="src/auth.py:authenticate",
            relation_types=["tests"]
        )

        # Find dependencies and dependents
        result = await kg_related(
            project_path="/projects/my-app",
            chunk_id="src/database.py:connect",
            relation_types=["dependencies", "dependents"]
        )

    Best Practice:
        Use this to understand the context around a piece of code:
        1. Find tests to understand expected behavior
        2. Find dependencies to understand requirements
        3. Find dependents to understand impact of changes
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

        # Get the chunk
        chunk = storage.get_chunk(chunk_id)
        if not chunk:
            return {
                "success": False,
                "error": f"Chunk not found: {chunk_id}"
            }

        # Define which edge types to query
        edge_type_map = {
            "tests": (EdgeType.TESTED_BY, "incoming"),
            "dependencies": (EdgeType.CALLS, "outgoing"),
            "dependents": (EdgeType.CALLS, "incoming"),
            "imports": (EdgeType.IMPORTS, "outgoing"),
            "imported_by": (EdgeType.IMPORTS, "incoming"),
            "commits": (EdgeType.MODIFIED_IN, "outgoing"),
            "rules": (EdgeType.VALIDATES, "incoming"),
            "contracts": (EdgeType.IMPLEMENTS, "outgoing"),
            "contains": (EdgeType.CONTAINS, "outgoing"),
            "contained_by": (EdgeType.CONTAINS, "incoming"),
        }

        # Filter to requested types or all
        types_to_query = relation_types or list(edge_type_map.keys())

        relations: Dict[str, List[str]] = {}
        details: Dict[str, List[Dict]] = {}

        for rel_type in types_to_query:
            if rel_type not in edge_type_map:
                continue

            edge_type, direction = edge_type_map[rel_type]

            if direction == "outgoing":
                edges = storage.get_edges_from(chunk_id, edge_type)
                related_ids = [e.target_id for e in edges]
            else:
                edges = storage.get_edges_to(chunk_id, edge_type)
                related_ids = [e.source_id for e in edges]

            if related_ids:
                relations[rel_type] = related_ids

                # Get details for related chunks
                related_chunks = storage.get_chunks(related_ids)
                details[rel_type] = [
                    {
                        "id": c.id,
                        "type": c.chunk_type.value,
                        "file_path": c.file_path,
                        "symbol_name": c.symbol_name,
                        "token_count": c.token_count,
                    }
                    for c in related_chunks
                ]

        # Build summary
        total_relations = sum(len(ids) for ids in relations.values())
        summary = f"Found {total_relations} related chunks across {len(relations)} relation types."

        return {
            "success": True,
            "chunk_id": chunk_id,
            "chunk_type": chunk.chunk_type.value,
            "chunk_file": chunk.file_path,
            "chunk_symbol": chunk.symbol_name,
            "relations": relations,
            "details": details,
            "summary": summary,
            "message": summary
        }

    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to find relations: {str(e)}"
        }
