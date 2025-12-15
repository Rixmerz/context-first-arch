"""
MCP Tool: context.load

Load full project context in a single call.

CFA v3: Now integrates with Knowledge Graph for intelligent context loading.
"""

from typing import Any, Dict, Optional
from pathlib import Path


async def context_load(
    project_path: str,
    use_knowledge_graph: bool = True,
    task: Optional[str] = None,
    token_budget: int = 20000
) -> Dict[str, Any]:
    """
    Load complete project context for LLM consumption.

    This is the OPTIMAL way to start working on a CFA project.
    CFA v3: Now uses Knowledge Graph for intelligent retrieval.

    Args:
        project_path: Path to CFA project
        use_knowledge_graph: Use KG for intelligent context (default: True)
        task: Optional task description for focused retrieval
        token_budget: Max tokens for KG context (default: 20000)

    Returns:
        Dictionary with:
            - success: Boolean
            - map: Contents of map.md (project overview)
            - task: Contents of current-task.md (current state)
            - quick_stats: File counts and status
            - kg_context: Knowledge Graph context (if available)
            - omission_summary: What was NOT loaded (CFA v3)

    Example:
        # Quick context load
        result = await context_load("/projects/my-app")

        # Task-focused context
        result = await context_load(
            "/projects/my-app",
            task="Fix authentication bug"
        )

    CFA v3 Benefits:
        - Intelligent context based on task
        - Omission transparency
        - Progressive disclosure for large codebases
    """
    try:
        path = Path(project_path)
        claude_dir = path / ".claude"

        if not claude_dir.exists():
            return {
                "success": False,
                "error": f"Not a CFA project: {project_path} (missing .claude/)"
            }

        # Read core context files
        map_file = claude_dir / "map.md"
        task_file = claude_dir / "current-task.md"

        map_content = map_file.read_text() if map_file.exists() else "(no map.md)"
        task_content = task_file.read_text() if task_file.exists() else "(no current-task.md)"

        # Quick stats
        impl_files = list((path / "impl").glob("*")) if (path / "impl").exists() else []
        contract_files = list((path / "contracts").glob("*.contract.md")) if (path / "contracts").exists() else []

        # Also check src/ for v2 projects
        src_files = list((path / "src").rglob("*.py")) if (path / "src").exists() else []

        result = {
            "success": True,
            "map": map_content,
            "task": task_content,
            "quick_stats": {
                "impl_files": len([f for f in impl_files if f.is_file()]) + len(src_files),
                "contracts": len(contract_files),
                "has_active_task": "IN_PROGRESS" in task_content or "BLOCKED" in task_content
            },
            "files_for_reference": {
                "map": ".claude/map.md",
                "task": ".claude/current-task.md",
                "decisions": ".claude/decisions.md"
            },
            "message": "Context loaded. You now have full project understanding."
        }

        # Try to enhance with Knowledge Graph if enabled
        if use_knowledge_graph:
            kg_result = await _try_kg_context(
                project_path=project_path,
                task=task,
                token_budget=token_budget
            )
            if kg_result:
                result["kg_status"] = kg_result.get("status", "unknown")
                if kg_result.get("status") == "active":
                    result["kg_context"] = kg_result.get("context", "")
                    result["kg_chunks"] = kg_result.get("chunks_loaded", 0)
                    result["omission_summary"] = kg_result.get("omission_summary", "")

                    if kg_result.get("omitted_count", 0) > 0:
                        result["tip"] = (
                            f"Loaded {kg_result.get('chunks_loaded', 0)} chunks. "
                            f"{kg_result.get('omitted_count', 0)} omitted - use kg.omitted to explore."
                        )

        return result

    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to load context: {str(e)}"
        }


async def _try_kg_context(
    project_path: str,
    task: Optional[str],
    token_budget: int
) -> Optional[Dict[str, Any]]:
    """Try to get context from Knowledge Graph."""
    try:
        from src.core.chunking import ChunkStorage, ContextRetriever

        path = Path(project_path)
        kg_db = path / ".claude" / "knowledge_graph.db"

        if not kg_db.exists():
            return {"status": "not_built"}

        storage = ChunkStorage(path)
        retriever = ContextRetriever(storage)

        # Use provided task or generic
        task_desc = task or "quick context load for project understanding"

        bundle = retriever.retrieve(
            task=task_desc,
            token_budget=token_budget,
            include_tests=False,
            compression_level=1
        )

        return {
            "status": "active",
            "chunks_loaded": len(bundle.chunks),
            "tokens_used": bundle.total_tokens,
            "omission_summary": bundle.omission_summary,
            "omitted_count": len(bundle.omitted_chunks),
            "context": bundle.to_markdown()[:15000]  # Limit context size
        }

    except Exception as e:
        return {"status": "error", "error": str(e)}
