"""
MCP Tool: kg.build

Build or update the Project Knowledge Graph.
"""

from typing import Any, Dict, List, Optional
from pathlib import Path

from src.features.knowledge_graph import build_knowledge_graph


async def kg_build(
    project_path: str,
    incremental: bool = False,
    changed_files: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Build or update the Project Knowledge Graph.

    The Knowledge Graph indexes all code, tests, configs, and metadata
    in your project for intelligent context retrieval.

    Args:
        project_path: Path to CFA project
        incremental: If True, only update changed files
        changed_files: List of changed file paths (for incremental builds)

    Returns:
        Dictionary with:
            - success: Boolean
            - mode: "full" or "incremental"
            - chunks_created: Number of chunks created
            - edges_created: Number of edges created
            - chunks_by_type: Breakdown by chunk type
            - edges_by_type: Breakdown by edge type
            - build_time_ms: Build time in milliseconds

    Examples:
        # Full rebuild
        result = await kg_build(project_path="/projects/my-app")

        # Incremental update after editing files
        result = await kg_build(
            project_path="/projects/my-app",
            incremental=True,
            changed_files=["src/auth.py", "src/user.py"]
        )

    Best Practice:
        Run full build when onboarding to a project.
        Use incremental builds after making changes.
        The graph is automatically built by kg.retrieve if needed.
    """
    try:
        path = Path(project_path)

        # Validate CFA project
        if not (path / ".claude").exists():
            return {
                "success": False,
                "error": "Not a CFA project (missing .claude/). Run project.init first."
            }

        # Build the graph
        result = await build_knowledge_graph(
            project_path=str(path),
            incremental=incremental,
            changed_files=changed_files
        )

        return {
            "success": True,
            "mode": result.get("mode", "full"),
            "chunks_created": result.get("chunks_created", 0),
            "edges_created": result.get("edges_created", 0),
            "chunks_by_type": result.get("chunks_by_type", {}),
            "edges_by_type": result.get("edges_by_type", {}),
            "build_time_ms": result.get("build_time_ms", 0),
            "message": (
                f"Knowledge Graph built successfully. "
                f"{result.get('chunks_created', 0)} chunks, "
                f"{result.get('edges_created', 0)} edges."
            )
        }

    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to build Knowledge Graph: {str(e)}"
        }
