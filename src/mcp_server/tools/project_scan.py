"""
MCP Tool: project.scan

Scan project and update map.md with current state.

CFA v3: Now also builds/updates the Knowledge Graph.
"""

from typing import Any, Dict
from pathlib import Path

from src.core.map_generator import update_map_file, generate_map, render_map


async def project_scan(
    project_path: str,
    build_knowledge_graph: bool = True
) -> Dict[str, Any]:
    """
    Scan project and update .claude/map.md.

    CFA v3: Also builds/updates the Knowledge Graph for intelligent retrieval.

    Analyzes all code to generate:
    - Entry points
    - File purpose index
    - Data flow
    - Current state
    - Knowledge Graph (CFA v3)

    Run this after making significant changes.

    Args:
        project_path: Path to CFA project
        build_knowledge_graph: Also build/update KG (default: True)

    Returns:
        Dictionary with:
            - success: Boolean
            - stats: Analysis statistics
            - map_preview: First 500 chars of generated map
            - kg_status: Knowledge Graph build status (CFA v3)

    Example:
        result = await project_scan("/projects/my-app")
        # map.md and Knowledge Graph are now updated
    """
    try:
        path = Path(project_path)
        claude_dir = path / ".claude"

        if not claude_dir.exists():
            return {
                "success": False,
                "error": f"Not a CFA project: {project_path} (missing .claude/)"
            }

        # Generate and update map
        stats = update_map_file(project_path)

        # Read back for preview
        map_content = (claude_dir / "map.md").read_text()

        result = {
            "success": True,
            "stats": stats,
            "file_updated": ".claude/map.md",
            "map_preview": map_content[:800] + "..." if len(map_content) > 800 else map_content,
            "message": f"Map updated: {stats['files_analyzed']} files analyzed, {stats['entry_points_found']} entry points found"
        }

        # Build Knowledge Graph if requested
        if build_knowledge_graph:
            kg_result = await _build_knowledge_graph(project_path)
            result["kg_status"] = kg_result.get("status", "unknown")
            if kg_result.get("success"):
                result["kg_chunks"] = kg_result.get("chunks", 0)
                result["kg_edges"] = kg_result.get("edges", 0)
                result["message"] += f". KG: {kg_result.get('chunks', 0)} chunks indexed."

        return result

    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to scan project: {str(e)}"
        }


async def _build_knowledge_graph(project_path: str) -> Dict[str, Any]:
    """Build or update the Knowledge Graph."""
    try:
        from src.core.chunking import (
            ChunkStorage, CodeChunker, ContractChunker,
            ConfigChunker, GraphBuilder, build_knowledge_graph
        )

        path = Path(project_path)
        result = build_knowledge_graph(path)

        return {
            "success": True,
            "status": "built",
            "chunks": result.get("chunks_created", 0),
            "edges": result.get("edges_created", 0),
        }

    except Exception as e:
        return {
            "success": False,
            "status": "error",
            "error": str(e)
        }
