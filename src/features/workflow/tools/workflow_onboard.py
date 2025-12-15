"""
MCP Tool: workflow.onboard

[START HERE] Generate initial project context for AI-assisted development.
Consolidates: onboard + check_onboard

CFA v3: Now integrates with Knowledge Graph for intelligent context retrieval.
"""

from typing import Any, Dict, Optional, List
from pathlib import Path

from src.features.workflow.core.onboarding import generate_onboarding, check_onboarding_status


async def workflow_onboard(
    project_path: str,
    check_only: bool = False,
    include_contracts: bool = True,
    include_decisions: bool = True,
    max_context_size: int = 50000,
    use_knowledge_graph: bool = True,
    task_hint: Optional[str] = None
) -> Dict[str, Any]:
    """
    [START HERE] Load full project context for new sessions.

    Primary entry point for AI-assisted development. Either loads
    complete project context or checks if refresh is needed.

    CFA v3: Now uses Knowledge Graph for intelligent, task-aware retrieval
    with full omission transparency.

    Args:
        project_path: Path to the project root
        check_only: If True, only check status without full onboarding
        include_contracts: Include contract summaries (default: True)
        include_decisions: Include architecture decisions (default: True)
        max_context_size: Maximum context size in characters (default: 50000)
        use_knowledge_graph: Use KG for intelligent retrieval (default: True)
        task_hint: Optional task description for KG-based retrieval

    Returns:
        When check_only=False (default):
            - success: Boolean
            - project_name: Name of the project
            - cfa_version: CFA version used
            - context: Full onboarding context
            - context_size: Size of context in characters
            - files_read: List of files included in context
            - truncated: Whether context was truncated
            - kg_status: Knowledge Graph status (if used)
            - omitted_summary: What was NOT loaded (CFA v3)

        When check_only=True:
            - success: Boolean
            - onboarded: Whether onboarding was performed
            - last_onboarding: Timestamp of last onboarding
            - hours_ago: Hours since last onboarding
            - files_changed_since: Files changed since onboarding
            - needs_refresh: Whether refresh is recommended
            - recommendation: Action recommendation

    Examples:
        # Full onboarding with Knowledge Graph (recommended)
        result = await workflow_onboard(project_path="/projects/my-app")

        # Task-aware onboarding
        result = await workflow_onboard(
            project_path="/projects/my-app",
            task_hint="Fix authentication bug in login flow"
        )

        # Quick status check
        status = await workflow_onboard(
            project_path="/projects/my-app",
            check_only=True
        )

        # Legacy mode (without Knowledge Graph)
        result = await workflow_onboard(
            project_path="/projects/my-app",
            use_knowledge_graph=False
        )

    Best Practice:
        ALWAYS run this at session start. CFA v3 provides:
        - Intelligent context based on task (via Knowledge Graph)
        - Omission transparency (what was NOT loaded)
        - Progressive disclosure for large codebases
    """
    try:
        if check_only:
            # Check status only
            result = check_onboarding_status(project_path=project_path)
            result["mode"] = "check"

            # Add KG status if available
            path = Path(project_path)
            kg_db = path / ".claude" / "knowledge_graph.db"
            result["kg_available"] = kg_db.exists()

            return result

        # Full onboarding
        result = generate_onboarding(
            project_path=project_path,
            include_contracts=include_contracts,
            include_decisions=include_decisions,
            max_context_size=max_context_size
        )
        result["mode"] = "full"

        # Try to enhance with Knowledge Graph if enabled
        if use_knowledge_graph:
            kg_result = await _try_kg_enhance(
                project_path=project_path,
                task_hint=task_hint,
                token_budget=max_context_size // 4  # Convert chars to approx tokens
            )
            if kg_result:
                result["kg_status"] = kg_result.get("status", "available")
                result["kg_chunks_loaded"] = kg_result.get("chunks_loaded", 0)
                result["omitted_summary"] = kg_result.get("omission_summary", "")
                result["kg_context"] = kg_result.get("context", "")

                # Add tip about omissions
                if kg_result.get("omitted_count", 0) > 0:
                    result["tip"] = (
                        f"Knowledge Graph loaded {kg_result.get('chunks_loaded', 0)} chunks. "
                        f"{kg_result.get('omitted_count', 0)} chunks omitted - use kg.omitted to see what."
                    )

        return result

    except FileNotFoundError as e:
        return {
            "success": False,
            "mode": "check" if check_only else "full",
            "error": f"Project not found: {str(e)}"
        }
    except Exception as e:
        return {
            "success": False,
            "mode": "check" if check_only else "full",
            "error": f"Onboarding failed: {str(e)}"
        }


async def _try_kg_enhance(
    project_path: str,
    task_hint: Optional[str],
    token_budget: int
) -> Optional[Dict[str, Any]]:
    """Try to enhance onboarding with Knowledge Graph context."""
    try:
        from src.core.chunking import ChunkStorage, ContextRetriever

        path = Path(project_path)
        kg_db = path / ".claude" / "knowledge_graph.db"

        if not kg_db.exists():
            return {"status": "not_built", "tip": "Run kg.build to enable intelligent retrieval"}

        storage = ChunkStorage(path)
        retriever = ContextRetriever(path, storage)

        # Use task hint or generic onboarding task
        task = task_hint or "general project understanding and onboarding"

        bundle = retriever.retrieve(
            task=task,
            token_budget=token_budget,
            include_tests=False,  # Keep onboarding focused
            compression=1  # NO_COMMENTS - moderate compression
        )

        return {
            "status": "active",
            "chunks_loaded": len(bundle.chunks),
            "tokens_used": bundle.total_tokens,
            "omission_summary": bundle.omission_summary,
            "omitted_count": len(bundle.omitted_chunks),
            "context": bundle.to_markdown()[:20000]  # Limit KG context size
        }

    except Exception as e:
        return {"status": "error", "error": str(e)}
